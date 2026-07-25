"""
SceneForge Transformers Caption Provider

Real implementation of `Capability.CAPTION` via Hugging Face
`transformers`' `image-text-to-text` pipeline (the current-generation
replacement for the older `image-to-text` task -- confirmed against
`transformers==5.14.1`'s actual installed source,
`transformers/pipelines/image_text_to_text.py`, not guessed).

The pipeline object is *injected*, not constructed internally:
`pipeline(task="image-text-to-text", model="Salesforce/blip-image-captioning-base")`
downloads model weights from the Hugging Face Hub on first use and
typically needs `torch` installed -- neither is a precondition this
package can assume (this very development sandbox has network access
to PyPI but not the Hugging Face Hub, and has no `torch` installed).
Injecting the pipeline instead:

  * makes this provider fully unit-testable without network access,
    `torch`, or downloaded weights (see
    `tests/contrib/test_transformers_caption.py`, which injects a
    lightweight fake satisfying `ImageTextToTextPipelineProtocol`)
  * lets a caller choose the model, device, and dtype explicitly -- a
    small captioning model on CPU and a large VLM on GPU are very
    different resource asks, and this provider shouldn't decide that
    silently (the same reasoning as `WhisperTranscribeProvider`, see
    `sceneforge/contrib/whisper/provider.py`'s module docstring)

This provider is intentionally *synchronous*, for the same reason
`WhisperTranscribeProvider` is: model inference is a blocking,
CPU/GPU-bound call with no async variant of its own. Wrap it with
`sceneforge.core.async_provider.SyncProviderAdapter` to run it under
`AsyncPipeline`'s bounded concurrency (ADR-0009) instead of captioning
a movie's frames one at a time.

Example:
    from transformers import pipeline
    from sceneforge.contrib.transformers_caption import TransformersCaptionProvider
    from sceneforge.core.async_provider import SyncProviderAdapter
    from sceneforge.core.async_pipeline import AsyncPipeline

    pipe = pipeline(
        task="image-text-to-text", model="Salesforce/blip-image-captioning-base"
    )
    provider = SyncProviderAdapter(TransformersCaptionProvider(pipe))
    pipeline_ = AsyncPipeline(provider, max_concurrency=2, timeout_seconds=120)
    batch = await pipeline_.run_many(scene_frames)

Only `ImageMedia` is accepted, even though `Capability.CAPTION` is
registered for both `ImageMedia` and `VideoMedia`
(`sceneforge/core/capability_registry.py`). Captioning a whole video is
a different, harder problem (which frame(s) represent it) than
captioning one already-extracted frame; this provider takes the
already-extracted-frame half of that problem, consistent with this
project's separation between `FRAME_EXTRACTION`
(`sceneforge.contrib.ffmpeg`) and per-frame analysis providers. A
future video-native captioner can register its own provider for the
same capability without this one claiming ground it doesn't cover.
"""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any, Protocol, runtime_checkable

from sceneforge.contrib.transformers_caption.caption_artifact import CaptionArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import ProviderError
from sceneforge.core.provider import Provider
from sceneforge.media.base import Media
from sceneforge.media.image import ImageMedia


@runtime_checkable
class ImageTextToTextPipelineProtocol(Protocol):
    """
    Structural contract matching `transformers.ImageTextToTextPipeline`
    closely enough that a real pipeline object (from
    `transformers.pipeline(task="image-text-to-text", ...)`) satisfies
    it without adaptation, while tests inject a lightweight fake with
    the same shape and no model weights.

    Modeled on the real class's documented usage
    (`pipe(image, text=prompt) -> [{"generated_text": "..."}]`), not
    guessed -- see this module's docstring.
    """

    def __call__(
        self, images: str, text: str | None = None, **kwargs: Any
    ) -> list[dict[str, str]]:
        """Return [{"generated_text": ...}] for the given image path/URL."""
        ...


class TransformersCaptionProvider(Provider):
    """
    Captions ImageMedia into one `CaptionArtifact` per image.

    Any keyword arguments accepted by
    `ImageTextToTextPipelineProtocol.__call__` (`max_new_tokens`,
    `num_beams`, ...) can be pinned at construction time via
    `**generate_kwargs`. `prompt` is passed as the pipeline's `text`
    conditioning argument -- some captioning models (BLIP) support an
    optional prefix prompt; pass `None` for models that don't use one.
    """

    def __init__(
        self,
        pipe: ImageTextToTextPipelineProtocol,
        prompt: str | None = None,
        **generate_kwargs: Any,
    ) -> None:
        self._pipe = pipe
        self._prompt = prompt
        self._generate_kwargs = generate_kwargs

    @property
    def name(self) -> str:
        return "transformers_caption"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.CAPTION})

    @property
    def execution_fingerprint(self) -> str:
        """
        Distinguish differently configured instances in `content_key()`.

        `prompt` and `generate_kwargs` are pinned at construction time
        and genuinely change what `run()` produces -- a
        `prompt="a photo of"` instance and a `prompt=None` instance
        captioning the same image are a different question, not a
        cache hit. Same reasoning as
        `WhisperTranscribeProvider.execution_fingerprint`
        (ADR-0024 Phase 0 item 2).
        """
        basis = json.dumps(
            {"prompt": self._prompt, "generate_kwargs": self._generate_kwargs},
            sort_keys=True,
            default=str,
        )
        return sha256(basis.encode("utf-8")).hexdigest()

    def run(self, media: Media) -> list[Artifact[Any]]:
        if not isinstance(media, ImageMedia):
            raise TypeError(f"Expected ImageMedia, got {type(media).__name__}")

        source = media.metadata.get("source")
        if not source:
            raise ProviderError(
                "Media has no 'source' path in metadata -- load it via a "
                "Local*Loader (or set metadata['source'] yourself) before "
                "captioning."
            )

        try:
            results = self._pipe(
                str(source), text=self._prompt, **self._generate_kwargs
            )
        except Exception as exc:  # noqa: BLE001 - re-branded, not swallowed
            raise ProviderError(f"captioning failed for '{source}': {exc}") from exc

        if not results:
            raise ProviderError(f"captioning returned no result for '{source}'")

        caption_text = results[0]["generated_text"].strip()
        return [
            CaptionArtifact(
                media_id=media.id,
                provider=self.name,
                payload=caption_text,
                prompt=self._prompt,
                source_frame_path=str(source),
            )
        ]
