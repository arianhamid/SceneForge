"""
SceneForge Caption Artifacts

Artifact produced by TransformersCaptionProvider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sceneforge.core.artifact import Artifact, ArtifactCategory, ArtifactKind
from sceneforge.core.storage import register_artifact_type


@register_artifact_type
@dataclass(frozen=True, slots=True)
class CaptionArtifact(Artifact[str]):
    """One generated caption for one image. `payload` is the caption text.

    `source_frame_path` carries the same cross-domain-correlation hook
    `FaceDetectionArtifact`/`OCRTextArtifact`/`ObjectDetectionArtifact`
    already have (ADR-0016) -- added here to match, not because a
    builder uses it yet (none does)."""

    media_id: UUID = field(default_factory=uuid4)
    prompt: str | None = None
    source_frame_path: str = ""
    kind: ArtifactKind = ArtifactKind.CAPTION
    category: ArtifactCategory = ArtifactCategory.ANALYSIS
    provider: str = "transformers_caption"
