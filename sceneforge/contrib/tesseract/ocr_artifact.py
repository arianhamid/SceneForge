"""
SceneForge OCR Artifacts

Artifact produced by TesseractOCRProvider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sceneforge.core.artifact import Artifact, ArtifactCategory, ArtifactKind
from sceneforge.core.storage import register_artifact_type


@register_artifact_type
@dataclass(frozen=True, slots=True)
class OCRTextArtifact(Artifact[str]):
    """
    A single recognized word (or word-group, per Tesseract's own
    segmentation), in pixel coordinates relative to the source image's
    top-left corner. `payload` is the recognized text.

    One artifact per recognized word rather than one per image keeps
    this the same shape as `FaceDetectionArtifact` -- a caller wanting
    the whole image's text joins the words themselves, the same way
    `SceneGroupingBuilder` joins transcript segments.
    """

    media_id: UUID = field(default_factory=uuid4)
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    confidence: float = 0.0
    word_index: int = 0
    source_frame_path: str = ""
    kind: ArtifactKind = ArtifactKind.OCR
    category: ArtifactCategory = ArtifactCategory.RECOGNITION
    provider: str = "tesseract_ocr"
