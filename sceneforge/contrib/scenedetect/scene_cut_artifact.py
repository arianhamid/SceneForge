"""
SceneForge Scene Cut Artifacts

Artifact produced by PySceneDetectProvider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sceneforge.core.artifact import Artifact, ArtifactCategory, ArtifactKind
from sceneforge.core.storage import register_artifact_type


@register_artifact_type
@dataclass(frozen=True, slots=True)
class SceneCutArtifact(Artifact[None]):
    """
    A single detected scene boundary: one contiguous shot.

    `scene_index` is this scene's position in viewing order, so
    downstream consumers (a future Knowledge Builder grouping frames
    by scene) can reconstruct ordering without re-sorting by timestamp.
    """

    media_id: UUID = field(default_factory=uuid4)
    scene_index: int = 0
    start_seconds: float = 0.0
    end_seconds: float = 0.0
    start_frame: int = 0
    end_frame: int = 0
    kind: ArtifactKind = ArtifactKind.SCENE_CUT
    category: ArtifactCategory = ArtifactCategory.ANALYSIS
    provider: str = "pyscenedetect"

    @property
    def duration_seconds(self) -> float:
        return self.end_seconds - self.start_seconds
