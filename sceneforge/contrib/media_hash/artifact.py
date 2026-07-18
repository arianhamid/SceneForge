"""
SceneForge Media Hash Artifact

Immutable artifact containing content hash of media.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.storage import register_artifact_type


@register_artifact_type
@dataclass(frozen=True, slots=True)
class MediaHashArtifact(Artifact[None]):
    """Artifact containing content hash of media."""

    media_id: UUID = field(default_factory=uuid4)
    hash_value: str = ""
    algorithm: str = ""
    source_type: str = ""  # "file" or "identity"
    kind: ArtifactKind = ArtifactKind.ARTIFACT
    provider: str = "media_hash"
