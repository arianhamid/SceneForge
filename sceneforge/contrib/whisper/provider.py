"""
SceneForge Whisper Transcription Provider

Real implementation of `Capability.TRANSCRIBE` via faster-whisper.

The model is *injected*, not constructed internally from a hardcoded
`model_size_or_path`: instantiating `faster_whisper.WhisperModel`
downloads weights from the Hugging Face Hub on first use, which many
environments (offline CI, sandboxes, this very development
environment) cannot reach. Injecting the model instead:

  * makes this provider fully unit-testable without network access or
    a GPU (see `tests/contrib/test_whisper_transcribe.py`, which
    injects a lightweight fake satisfying `WhisperModelProtocol`)
  * lets a caller choose model size, device, and compute type
    explicitly -- a tiny model on CPU and a large model on GPU are
    very different resource asks, and this provider shouldn't decide
    that silently

This provider is intentionally *synchronous*: faster-whisper's own
`transcribe()` call is a blocking, CPU/GPU-bound operation with no
async variant of its own. Wrap it with
`sceneforge.core.async_provider.SyncProviderAdapter` to run it under
`AsyncPipeline`'s bounded concurrency (ADR-0009) instead of processing
a movie's scenes one at a time -- see the module docstring example
below.

Example:
    from faster_whisper import WhisperModel
    from sceneforge.contrib.whisper import WhisperTranscribeProvider
    from sceneforge.core.async_provider import SyncProviderAdapter
    from sceneforge.core.async_pipeline import AsyncPipeline

    model = WhisperModel("small", device="cpu", compute_type="int8")
    provider = SyncProviderAdapter(WhisperTranscribeProvider(model))
    pipeline = AsyncPipeline(provider, max_concurrency=2, timeout_seconds=300)
    batch = await pipeline.run_many(scene_audio_clips)
"""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any, Protocol, runtime_checkable

from sceneforge.contrib.whisper.transcript_artifact import TranscriptSegmentArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import ProviderError
from sceneforge.core.provider import Provider
from sceneforge.media.audio import AudioMedia
from sceneforge.media.base import Media
from sceneforge.media.video import VideoMedia


@runtime_checkable
class WhisperSegmentLike(Protocol):
    start: float
    end: float
    text: str


@runtime_checkable
class WhisperTranscriptionInfoLike(Protocol):
    language: str


@runtime_checkable
class WhisperModelProtocol(Protocol):
    """
    Structural contract matching `faster_whisper.WhisperModel` closely
    enough that a real `WhisperModel` satisfies it without adaptation,
    while tests inject a lightweight fake with the same shape and no
    model weights.
    """

    def transcribe(
        self, audio: str, **kwargs: Any
    ) -> tuple[Any, WhisperTranscriptionInfoLike]:
        """Return (segments, info) -- matches faster_whisper.WhisperModel.transcribe."""
        ...


class WhisperTranscribeProvider(Provider):
    """
    Transcribes AudioMedia (or VideoMedia -- faster-whisper extracts
    audio from video files itself) into one `TranscriptSegmentArtifact`
    per detected speech segment.

    Any keyword arguments accepted by `WhisperModelProtocol.transcribe`
    (`language`, `beam_size`, `vad_filter`, ...) can be pinned at
    construction time via `**transcribe_kwargs`.
    """

    def __init__(self, model: WhisperModelProtocol, **transcribe_kwargs: Any) -> None:
        self._model = model
        self._transcribe_kwargs = transcribe_kwargs

    @property
    def name(self) -> str:
        return "whisper_transcribe"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.TRANSCRIBE})

    @property
    def execution_fingerprint(self) -> str:
        """
        Distinguish differently configured instances in `content_key()`.

        `transcribe_kwargs` (`language`, `beam_size`, `vad_filter`, ...)
        is pinned at construction time and genuinely changes what
        `run()` produces -- a `language="en"` instance and a
        `language="fr"` instance transcribing the same file are a
        different question, not a cache hit. This is the concrete case
        the 2026-07-22 implementation review reproduced live: before
        this override, both instances shared one `content_key()` (name
        and version only), so the second one's cached result could
        silently mask the first's.
        """
        basis = json.dumps(self._transcribe_kwargs, sort_keys=True, default=str)
        return sha256(basis.encode("utf-8")).hexdigest()

    def run(self, media: Media) -> list[Artifact[Any]]:
        if not isinstance(media, (AudioMedia, VideoMedia)):
            raise TypeError(
                f"Expected AudioMedia or VideoMedia, got {type(media).__name__}"
            )

        source = media.metadata.get("source")
        if not source:
            raise ProviderError(
                "Media has no 'source' path in metadata -- load it via a "
                "Local*Loader (or set metadata['source'] yourself) before "
                "transcribing."
            )

        try:
            segments, info = self._model.transcribe(
                str(source), **self._transcribe_kwargs
            )
        except Exception as exc:  # noqa: BLE001 - re-branded, not swallowed
            raise ProviderError(f"transcription failed for '{source}': {exc}") from exc

        artifacts: list[Artifact[Any]] = []
        for index, segment in enumerate(segments):
            artifacts.append(
                TranscriptSegmentArtifact(
                    media_id=media.id,
                    provider=self.name,
                    payload=segment.text.strip(),
                    segment_index=index,
                    start_seconds=segment.start,
                    end_seconds=segment.end,
                    language=info.language,
                )
            )
        return artifacts
