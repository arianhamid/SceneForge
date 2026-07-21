"""
SceneForge Tesseract OCR Provider

Real implementation of `Capability.OCR`, using the Tesseract OCR
engine via `pytesseract`. Like `sceneforge.contrib.opencv`, this needs
no dependency injection: Tesseract's trained language data
(`eng.traineddata`) ships as a system package
(`apt install tesseract-ocr`), not downloaded at runtime by the
provider itself -- the same "bundled, not fetched" shape as OpenCV's
Haar cascades (ADR-0015), and the reason this provider is real rather
than dependency-injected like `WhisperTranscribeProvider`.

Unlike `OpenCVFaceDetectionProvider` and `WhisperTranscribeProvider`,
this provider's positive-detection claim *is* verified in this
environment: `tests/contrib/test_tesseract_integration.py` renders
real text into a real image with a real bundled font and confirms
Tesseract reads it back correctly. No network access or unavailable
fixture blocks that here, unlike faces or speech.
"""

from __future__ import annotations

from typing import Any

from sceneforge.contrib.tesseract.ocr_artifact import OCRTextArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import ProviderError
from sceneforge.core.provider import Provider
from sceneforge.media.base import Media
from sceneforge.media.image import ImageMedia

DEFAULT_LANGUAGE = "eng"
DEFAULT_MIN_CONFIDENCE = 0.0


class TesseractOCRProvider(Provider):
    """
    Recognizes text in an image via the Tesseract OCR engine.

    ``min_confidence`` filters out Tesseract's own low-confidence noise
    (regions it examined but isn't confident contain real text --
    reported as -1 or a low score, not omitted from its raw output).
    Tesseract's confidence scores are 0-100; ``min_confidence`` is
    expressed the same way for direct comparison against Tesseract's
    own documented range, not normalized to 0-1 like some other
    providers' internal thresholds.
    """

    def __init__(
        self,
        language: str = DEFAULT_LANGUAGE,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
    ) -> None:
        self._language = language
        self._min_confidence = min_confidence

    @property
    def name(self) -> str:
        return "tesseract_ocr"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.OCR})

    def run(self, media: Media) -> list[Artifact[Any]]:
        if not isinstance(media, ImageMedia):
            raise TypeError(f"Expected ImageMedia, got {type(media).__name__}")

        source = media.metadata.get("source")
        if not source:
            raise ProviderError(
                "ImageMedia has no 'source' path in metadata -- load it via "
                "LocalImageLoader (or set metadata['source'] yourself) before "
                "running OCR."
            )

        try:
            import pytesseract
            from PIL import Image
        except ImportError as exc:
            raise ProviderError(
                "The 'pytesseract' and 'Pillow' packages, plus the "
                "'tesseract-ocr' system package, are required for "
                "TesseractOCRProvider."
            ) from exc

        try:
            image = Image.open(str(source))
            data = pytesseract.image_to_data(
                image, lang=self._language, output_type=pytesseract.Output.DICT
            )
        except Exception as exc:  # noqa: BLE001 - re-branded, not swallowed
            raise ProviderError(f"OCR failed for '{source}': {exc}") from exc

        artifacts: list[Artifact[Any]] = []
        word_index = 0
        for i in range(len(data["text"])):
            text = data["text"][i].strip()
            confidence = float(data["conf"][i])
            if not text or confidence < self._min_confidence:
                continue
            artifacts.append(
                OCRTextArtifact(
                    media_id=media.id,
                    provider=self.name,
                    payload=text,
                    x=int(data["left"][i]),
                    y=int(data["top"][i]),
                    width=int(data["width"][i]),
                    height=int(data["height"][i]),
                    confidence=confidence,
                    word_index=word_index,
                    source_frame_path=str(source),
                )
            )
            word_index += 1
        return artifacts
