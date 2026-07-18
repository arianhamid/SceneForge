"""
SceneForge OpenCV Face Detection Provider

Real implementation of `Capability.FACE_DETECTION`, using OpenCV's
bundled Haar cascade classifier. Unlike `sceneforge.contrib.whisper`,
this needs no dependency injection: the classifier's trained weights
ship inside the `opencv-python`/`opencv-python-headless` package
itself (`cv2.data.haarcascades`), so there's no network access, no
separate model download, and no reason not to construct it directly --
the same "algorithmic, no external weights" shape as
`sceneforge.contrib.scenedetect`, just for a different capability.

Honesty about test coverage: this environment has no real photograph
of a face to test a positive detection against (no network access to
fetch one). Tests here prove the real mechanics -- a real bundled
cascade file, real OpenCV decoding, correct artifact shaping, correct
error handling -- and prove the negative path with certainty (solid-
color and synthetic-shape images reliably produce zero detections).
The "detects an actual face in an actual photo" claim is real (this is
production OpenCV code, not a stub) but untested in this sandbox --
verify it against a real photo before relying on it in production, the
same caveat `WhisperTranscribeProvider` carries for real model weights.

Every produced `FaceDetectionArtifact.source_frame_path` is set to the
decoded image's own `metadata["source"]` path -- when that ImageMedia
is a still frame extracted from a video (as opposed to a standalone
photo), this is the same path `FrameExtractionArtifact.frame_path`
carries, and is what a cross-domain Knowledge Builder correlates on
(matching file paths) rather than needing `media_id` relinking. See
`docs/adr/0016-cross-domain-knowledge-builder.md`.
"""

from __future__ import annotations

from typing import Any

from sceneforge.contrib.opencv.face_detection_artifact import FaceDetectionArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import ProviderError
from sceneforge.core.provider import Provider
from sceneforge.media.base import Media
from sceneforge.media.image import ImageMedia

DEFAULT_CASCADE = "haarcascade_frontalface_default.xml"
DEFAULT_SCALE_FACTOR = 1.1
DEFAULT_MIN_NEIGHBORS = 5


class OpenCVFaceDetectionProvider(Provider):
    """
    Detects faces in an image via OpenCV's Haar cascade classifier.

    ``scale_factor``/``min_neighbors`` are passed straight through to
    ``cv2.CascadeClassifier.detectMultiScale`` -- OpenCV's own
    defaults (1.1 / 5) are reasonable starting points; lower
    ``min_neighbors`` detects more (including more false positives),
    higher detects fewer but more confidently.
    """

    def __init__(
        self,
        cascade_name: str = DEFAULT_CASCADE,
        scale_factor: float = DEFAULT_SCALE_FACTOR,
        min_neighbors: int = DEFAULT_MIN_NEIGHBORS,
    ) -> None:
        self._cascade_name = cascade_name
        self._scale_factor = scale_factor
        self._min_neighbors = min_neighbors

    @property
    def name(self) -> str:
        return "opencv_face_detection"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.FACE_DETECTION})

    def run(self, media: Media) -> list[Artifact[Any]]:
        if not isinstance(media, ImageMedia):
            raise TypeError(f"Expected ImageMedia, got {type(media).__name__}")

        source = media.metadata.get("source")
        if not source:
            raise ProviderError(
                "ImageMedia has no 'source' path in metadata -- load it via "
                "LocalImageLoader (or set metadata['source'] yourself) before "
                "detecting faces."
            )

        try:
            import cv2
        except ImportError as exc:
            raise ProviderError(
                "The 'opencv-python' (or 'opencv-python-headless') package is "
                "required for OpenCVFaceDetectionProvider."
            ) from exc

        cascade_path = cv2.data.haarcascades + self._cascade_name  # type: ignore[attr-defined]
        classifier = cv2.CascadeClassifier(cascade_path)
        if classifier.empty():
            raise ProviderError(f"Could not load cascade '{self._cascade_name}'")

        image = cv2.imread(str(source))
        if image is None:
            raise ProviderError(f"OpenCV could not decode image at '{source}'")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        try:
            detections = classifier.detectMultiScale(
                gray,
                scaleFactor=self._scale_factor,
                minNeighbors=self._min_neighbors,
            )
        except Exception as exc:  # noqa: BLE001 - re-branded, not swallowed
            raise ProviderError(f"face detection failed for '{source}': {exc}") from exc

        artifacts: list[Artifact[Any]] = []
        for index, (x, y, w, h) in enumerate(detections):
            artifacts.append(
                FaceDetectionArtifact(
                    media_id=media.id,
                    provider=self.name,
                    x=int(x),
                    y=int(y),
                    width=int(w),
                    height=int(h),
                    face_index=index,
                    source_frame_path=str(source),
                )
            )
        return artifacts
