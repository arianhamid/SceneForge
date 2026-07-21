"""
SceneForge Face Detection Artifacts

Artifact produced by OpenCVFaceDetectionProvider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sceneforge.core.artifact import Artifact, ArtifactCategory, ArtifactKind
from sceneforge.core.storage import register_artifact_type


@register_artifact_type
@dataclass(frozen=True, slots=True)
class FaceDetectionArtifact(Artifact[None]):
    """
    A single detected face's bounding box, in pixel coordinates
    relative to the source image's top-left corner.

    `media_id` belongs to whatever `ImageMedia` was actually decoded
    -- when that's a still frame extracted from a video (rather than a
    standalone photo), `media_id` is the *frame's own* generated id,
    not the source video's. `source_frame_path` carries the frame file
    path so a Knowledge Builder can correlate this detection back to
    the `FrameExtractionArtifact` (and, via that, the scene) it came
    from -- see `docs/adr/0016-cross-domain-knowledge-builder.md`.
    """

    media_id: UUID = field(default_factory=uuid4)
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    face_index: int = 0
    source_frame_path: str = ""
    kind: ArtifactKind = ArtifactKind.FACE_DETECTION
    category: ArtifactCategory = ArtifactCategory.DETECTION
    provider: str = "opencv_face_detection"
