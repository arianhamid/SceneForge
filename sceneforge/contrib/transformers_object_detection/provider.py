"""
SceneForge Transformers Object Detection Provider

Real implementation of `Capability.OBJECT_DETECTION` via Hugging Face
`transformers`' `object-detection` pipeline. Confirmed against
`transformers==5.14.1`'s actual installed source,
`transformers/pipelines/object_detection.py`, not guessed:

    >>> detector = pipeline(model="facebook/detr-resnet-50")
    >>> detector("...parrots.png")
    [{'score': 0.997, 'label': 'bird',
      'box': {'xmin': 69, 'ymin': 171, 'xmax': 396, 'ymax': 507}}, ...]

This is the second real provider feeding the Facts rung
(`sceneforge.contrib.transformers_caption.TransformersCaptionProvider`
was the first) -- deliberately built to test whether
`FactExtractionBuilder`'s "one Artifact becomes one Fact" shape
actually generalizes, rather than being a coincidence of captioning's
specific structure. See `sceneforge/knowledge/fact_extraction_builder.py`
for what that comparison found.

Same dependency-injection reasoning as
`sceneforge.contrib.transformers_caption` and
`sceneforge.contrib.whisper`: real weights need Hugging Face Hub
access this environment doesn't have, so the pipeline object is
injected, not constructed internally. See either module's docstring
for the full reasoning; not repeated here.

One real difference from captioning that this second case surfaced:
an empty result (`[]`, no objects above the confidence threshold) is
a legitimate, meaningful outcome here -- "nothing detected" -- not a
failure. `TransformersCaptionProvider` treats an empty result as an
error, because a captioning model is expected to produce exactly one
caption per image; an object detector producing zero detections for a
blank wall is the model working correctly. This is exactly the kind
of thing a second real case is supposed to surface, and exactly why
this project waits for one before generalizing a shared shape.

Only `ImageMedia` is accepted, for the same reason
`TransformersCaptionProvider` only accepts it -- see that provider's
module docstring.
"""

from __future__ import annotations

import json
from hashlib import sha256
from typing import Any, Protocol, TypedDict, runtime_checkable

from sceneforge.contrib.transformers_object_detection.object_detection_artifact import (
    ObjectDetectionArtifact,
)
from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import ProviderError
from sceneforge.core.provider import Provider
from sceneforge.media.base import Media
from sceneforge.media.image import ImageMedia


class _BoundingBox(TypedDict):
    xmin: int
    ymin: int
    xmax: int
    ymax: int


class _Detection(TypedDict):
    score: float
    label: str
    box: _BoundingBox


@runtime_checkable
class ObjectDetectionPipelineProtocol(Protocol):
    """
    Structural contract matching `transformers.ObjectDetectionPipeline`
    closely enough that a real pipeline object (from
    `transformers.pipeline(task="object-detection", ...)`) satisfies it
    without adaptation. Modeled on the real class's documented usage,
    not guessed -- see this module's docstring.
    """

    def __call__(
        self, images: str, threshold: float | None = None, **kwargs: Any
    ) -> list[_Detection]:
        """Return [{"score", "label", "box": {"xmin", "ymin", "xmax", "ymax"}}, ...]
        for the given image path/URL. An empty list means no detections
        above `threshold`, not an error."""
        ...


class TransformersObjectDetectionProvider(Provider):
    """
    Detects objects in ImageMedia into one `ObjectDetectionArtifact` per
    detection.

    An empty result (no objects above `threshold`) produces an empty
    artifact list, not an error -- see this module's docstring.
    """

    def __init__(
        self,
        pipe: ObjectDetectionPipelineProtocol,
        threshold: float | None = None,
        **detect_kwargs: Any,
    ) -> None:
        self._pipe = pipe
        self._threshold = threshold
        self._detect_kwargs = detect_kwargs

    @property
    def name(self) -> str:
        return "transformers_object_detection"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.OBJECT_DETECTION})

    @property
    def execution_fingerprint(self) -> str:
        """Same reasoning as `TransformersCaptionProvider.execution_fingerprint`
        (ADR-0024 Phase 0 item 2): `threshold` and `detect_kwargs` genuinely
        change what `run()` produces."""
        basis = json.dumps(
            {"threshold": self._threshold, "detect_kwargs": self._detect_kwargs},
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
                "detecting objects."
            )

        kwargs: dict[str, Any] = dict(self._detect_kwargs)
        if self._threshold is not None:
            kwargs["threshold"] = self._threshold

        try:
            detections = self._pipe(str(source), **kwargs)
        except Exception as exc:  # noqa: BLE001 - re-branded, not swallowed
            raise ProviderError(
                f"object detection failed for '{source}': {exc}"
            ) from exc

        return [
            ObjectDetectionArtifact(
                media_id=media.id,
                provider=self.name,
                label=detection["label"],
                score=detection["score"],
                x_min=detection["box"]["xmin"],
                y_min=detection["box"]["ymin"],
                x_max=detection["box"]["xmax"],
                y_max=detection["box"]["ymax"],
                detection_index=i,
                source_frame_path=str(source),
            )
            for i, detection in enumerate(detections)
        ]
