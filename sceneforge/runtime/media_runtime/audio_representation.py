"""
SceneForge Audio Representation

Execution-time representation of audio data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class AudioChunkRepresentation:
    """
    Execution-time representation of an audio chunk.

    This is NOT a domain object. It exists only during processing.
    """

    media_id: UUID
    start_time: float  # seconds
    end_time: float  # seconds
    sample_rate: int
    channels: int
    dtype: str
    data: Any  # np.ndarray or similar

    id: UUID = field(default_factory=uuid4)

    @property
    def duration(self) -> float:
        """Duration of this chunk in seconds."""
        return self.end_time - self.start_time


@dataclass(frozen=True, slots=True)
class AudioRepresentation:
    """
    Execution-time representation of audio data.

    Contains metadata about the audio and a method to access chunks.
    Audio is decoded on-demand, not stored in memory.
    """

    media_id: UUID
    duration: float
    sample_rate: int
    channels: int
    bit_depth: int

    id: UUID = field(default_factory=uuid4)