"""
SceneForge Image Media

Immutable representation of an image resource.
"""

from __future__ import annotations

from dataclasses import dataclass

from .base import Media


@dataclass(frozen=True, slots=True, kw_only=True)
class ImageMedia(Media):
    """
    Immutable representation of an image.

    Contains no decoding logic — processing is delegated to Providers.
    """

    width: int
    height: int
    format: str

    @classmethod
    def from_dimensions(
        cls, name: str, width: int, height: int, format: str
    ) -> ImageMedia:
        return cls(name=name, width=width, height=height, format=format)

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height

    @property
    def pixel_count(self) -> int:
        return self.width * self.height