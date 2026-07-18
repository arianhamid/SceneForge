"""
SceneForge Transcript Segment Artifacts

Artifact produced by WhisperTranscribeProvider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.storage import register_artifact_type


@register_artifact_type
@dataclass(frozen=True, slots=True)
class TranscriptSegmentArtifact(Artifact[str]):
    """One transcribed speech segment. `payload` is the segment's text."""

    media_id: UUID = field(default_factory=uuid4)
    segment_index: int = 0
    start_seconds: float = 0.0
    end_seconds: float = 0.0
    language: str = "unknown"
    kind: ArtifactKind = ArtifactKind.TRANSCRIPT
    provider: str = "whisper_transcribe"
