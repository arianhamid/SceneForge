"""
SceneForge Image Info Provider

Extracts metadata from image media.
"""

from __future__ import annotations

from typing import Any

from sceneforge.contrib.image_info.artifacts import ImageInfoArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.provider import Provider
from sceneforge.media.base import Media
from sceneforge.media.image import ImageMedia


class ImageInfoProvider(Provider):
    """
    Provider that extracts metadata from images.

    Produces:
        - width
        - height
        - aspect_ratio
        - pixel_count
        - format
    """

    @property
    def name(self) -> str:
        return "image_info"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset()

    def run(self, media: Media) -> list[Artifact[Any]]:
        """
        Extract metadata from image media.

        Args:
            media: ImageMedia to extract metadata from.

        Returns:
            List containing ImageInfoArtifact.

        Raises:
            TypeError: If media is not ImageMedia.
        """
        if not isinstance(media, ImageMedia):
            raise TypeError(f"Expected ImageMedia, got {type(media).__name__}")

        return [
            ImageInfoArtifact(
                media_id=media.id,
                width=media.width,
                height=media.height,
                aspect_ratio=media.aspect_ratio,
                pixel_count=media.pixel_count,
                fmt=media.fmt,
            )
        ]
