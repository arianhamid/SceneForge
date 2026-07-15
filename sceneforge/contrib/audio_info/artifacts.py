"""
SceneForge Audio Info Artifacts

Artifacts produced by AudioInfoProvider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sceneforge.core.artifact import Artifact, ArtifactKind


@dataclass(frozen=True, slots=True)
class AudioInfoArtifact(Artifact[None]):
    """Artifact containing audio metadata."""

    media_id: UUID = field(default_factory=uuid4)
    duration: float = 0.0
    sample_rate: int = 0
    channels: int = 0
    bit_depth: int = 0
    kind: ArtifactKind = ArtifactKind.ARTIFACT
    provider: str = "audio_info"
