"""
SceneForge Frame Extraction Artifacts

Artifact produced by FFmpegFrameExtractionProvider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sceneforge.core.artifact import Artifact, ArtifactCategory, ArtifactKind
from sceneforge.core.storage import register_artifact_type


@register_artifact_type
@dataclass(frozen=True, slots=True)
class FrameExtractionArtifact(Artifact[None]):
    """
    A single frame extracted from a video.

    Carries a path to the extracted frame on disk rather than raw
    pixel data -- Artifacts are meant to be small, serializable
    observations (see ADR guidance and `sceneforge.core.storage`),
    not payload for the pixels themselves.
    """

    media_id: UUID = field(default_factory=uuid4)
    frame_path: str = ""
    timestamp_seconds: float = 0.0
    frame_index: int = 0
    kind: ArtifactKind = ArtifactKind.FRAME
    category: ArtifactCategory = ArtifactCategory.DERIVED
    provider: str = "ffmpeg_frame_extraction"
