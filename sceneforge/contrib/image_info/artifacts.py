"""
SceneForge Image Info Artifacts

Artifacts produced by ImageInfoProvider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.storage import register_artifact_type


@register_artifact_type
@dataclass(frozen=True, slots=True)
class ImageInfoArtifact(Artifact[None]):
    """Artifact containing image metadata."""

    media_id: UUID = field(default_factory=uuid4)
    width: int = 0
    height: int = 0
    aspect_ratio: float = 0.0
    pixel_count: int = 0
    fmt: str = ""
    kind: ArtifactKind = ArtifactKind.ARTIFACT
    provider: str = "image_info"
