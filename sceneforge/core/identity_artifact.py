"""
SceneForge Identity Artifact

Immutable artifact representing successful provider execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from sceneforge.core.artifact import Artifact, ArtifactKind


@dataclass(frozen=True, slots=True)
class IdentityArtifact(Artifact[None]):
    """
    Artifact representing successful provider execution.

    Used by IdentityProvider to prove the pipeline works.
    """

    media_id: UUID = field(default_factory=UUID)

    kind: ArtifactKind = ArtifactKind.ARTIFACT

    provider: str = "unknown"
