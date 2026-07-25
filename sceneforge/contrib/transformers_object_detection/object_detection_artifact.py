"""
SceneForge Object Detection Artifacts

Artifact produced by TransformersObjectDetectionProvider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sceneforge.core.artifact import Artifact, ArtifactCategory, ArtifactKind
from sceneforge.core.storage import register_artifact_type


@register_artifact_type
@dataclass(frozen=True, slots=True)
class ObjectDetectionArtifact(Artifact[None]):
    """
    A single detected object's label, confidence score, and bounding
    box, in pixel coordinates relative to the source image's top-left
    corner.

    Deliberately mirrors `FaceDetectionArtifact`'s shape
    (`sceneforge/contrib/opencv/face_detection_artifact.py`) -- one
    Artifact per detection, not one Artifact holding a list, so a
    Knowledge Builder can filter and aggregate detections the same way
    it already does for faces. `source_frame_path` carries the same
    cross-domain-correlation hook `FaceDetectionArtifact` already has
    (ADR-0016), unused by any builder yet, same as there.
    """

    media_id: UUID = field(default_factory=uuid4)
    label: str = ""
    score: float = 0.0
    x_min: int = 0
    y_min: int = 0
    x_max: int = 0
    y_max: int = 0
    detection_index: int = 0
    source_frame_path: str = ""
    kind: ArtifactKind = ArtifactKind.OBJECT_DETECTION
    category: ArtifactCategory = ArtifactCategory.DETECTION
    provider: str = "transformers_object_detection"
