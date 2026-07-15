"""
SceneForge Decoder Protocol

Protocol for decoding media into representations.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from sceneforge.media.base import Media


@runtime_checkable
class Decoder(Protocol):
    """
    Protocol for decoding media into representations.

    Decoders are infrastructure services that convert Media objects
    into representations. Providers request decoding, never perform it.
    """

    def decode(self, media: Media) -> Any:
        """
        Decode media into a representation.

        Args:
            media: The media object to decode.

        Returns:
            A representation (ImageRepresentation, VideoRepresentation, etc.)
        """
        ...