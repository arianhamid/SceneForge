"""
SceneForge Video Representation

Execution-time representation of video data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class VideoFrameRepresentation:
    """
    Execution-time representation of a single video frame.

    This is NOT a domain object. It exists only during processing.
    """

    media_id: UUID
    frame_index: int
    timestamp: float  # seconds
    width: int
    height: int
    dtype: str
    shape: tuple[int, ...]
    data: Any  # np.ndarray or similar

    id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True, slots=True)
class VideoRepresentation:
    """
    Execution-time representation of video data.

    Contains metadata about the video and a method to access frames.
    Frames are decoded on-demand, not stored in memory.
    """

    media_id: UUID
    duration: float
    fps: float
    frame_count: int
    width: int
    height: int

    id: UUID = field(default_factory=uuid4)