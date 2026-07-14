"""
SceneForge Audio Media

Immutable representation of an audio resource.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import Media


@dataclass(frozen=True, slots=True, kw_only=True)
class AudioMedia(Media):
    """
    Immutable representation of an audio file.

    Contains no decoding logic — processing is delegated to Providers.
    """

    duration: float
    sample_rate: int
    channels: int
    bit_depth: int = field(default=16)

    @classmethod
    def from_file(
        cls,
        name: str,
        duration: float,
        sample_rate: int,
        channels: int,
        bit_depth: int = 16,
    ) -> AudioMedia:
        return cls(
            name=name,
            duration=duration,
            sample_rate=sample_rate,
            channels=channels,
            bit_depth=bit_depth,
        )
