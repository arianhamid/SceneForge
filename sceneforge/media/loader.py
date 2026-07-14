"""
SceneForge Media Loader

Protocol defining the contract for loading media objects.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .base import Media


@runtime_checkable
class MediaLoader(Protocol):
    """
    Protocol for loading media objects.

    Any class with a load() method returning Media participates.
    Implementations don't need to inherit from this protocol.
    """

    def load(self) -> Media:
        """Load and return a Media object."""
        ...
