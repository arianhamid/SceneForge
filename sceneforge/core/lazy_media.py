"""
SceneForge Lazy Media

Wrapper that defers decoding until needed.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sceneforge.media.base import Media


class LazyMedia:
    """
    Wrapper that defers decoding until needed.

    Providers can request decoded data through the decoder,
    but decoding only happens when actually requested.
    """

    def __init__(self, media: Media, decoder: Any = None) -> None:
        """
        Initialize LazyMedia.

        Args:
            media: The underlying media object.
            decoder: Optional decoder for decoding.
        """
        self._media = media
        self._decoder = decoder
        self._decoded = None

    @property
    def media(self) -> Media:
        """Return the underlying media."""
        return self._media

    @property
    def id(self) -> UUID:
        """Return the media ID."""
        return self._media.id

    @property
    def name(self) -> str:
        """Return the media name."""
        return self._media.name

    def decode(self) -> Any:
        """
        Decode the media if not already decoded.

        Returns:
            The decoded representation.
        """
        if self._decoded is None:
            if self._decoder is None:
                raise ValueError("No decoder available")
            self._decoded = self._decoder.decode(self._media)
        return self._decoded

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to underlying media."""
        return getattr(self._media, name)
