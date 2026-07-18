"""
SceneForge Audio Info Provider

Extracts metadata from audio media.
"""

from __future__ import annotations

from typing import Any

from sceneforge.contrib.audio_info.artifacts import AudioInfoArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.provider import Provider
from sceneforge.media.audio import AudioMedia
from sceneforge.media.base import Media


class AudioInfoProvider(Provider):
    """
    Provider that extracts metadata from audio.

    Produces:
        - duration
        - sample_rate
        - channels
        - bit_depth
    """

    @property
    def name(self) -> str:
        return "audio_info"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset()  # No special capabilities needed for metadata

    def run(self, media: Media) -> list[Artifact[Any]]:
        """
        Extract metadata from audio media.

        Args:
            media: AudioMedia to extract metadata from.

        Returns:
            List containing AudioInfoArtifact.

        Raises:
            TypeError: If media is not AudioMedia.
        """
        if not isinstance(media, AudioMedia):
            raise TypeError(f"Expected AudioMedia, got {type(media).__name__}")

        return [
            AudioInfoArtifact(
                media_id=media.id,
                duration=media.duration,
                sample_rate=media.sample_rate,
                channels=media.channels,
                bit_depth=media.bit_depth,
            )
        ]
