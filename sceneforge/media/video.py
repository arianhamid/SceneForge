"""
SceneForge Video Media

Immutable representation of a video resource.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .base import Media


@dataclass(frozen=True, slots=True, kw_only=True)
class VideoMedia(Media):
    """
    Immutable representation of a video.

    Contains no decoding logic — processing is delegated to Providers.
    """

    duration: float
    codec: str
    fps: float

    @classmethod
    def from_file(
        cls, name: str, duration: float, codec: str, fps: float
    ) -> VideoMedia:
        return cls(name=name, duration=duration, codec=codec, fps=fps)

    @classmethod
    def from_path(
        cls, path: Path, duration: float, codec: str, fps: float
    ) -> VideoMedia:
        return cls(name=path.name, duration=duration, codec=codec, fps=fps)

    @property
    def frame_count(self) -> int:
        return int(self.duration * self.fps)
