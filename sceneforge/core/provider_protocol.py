"""
SceneForge Provider Protocol

Protocol defining the contract for processing media into artifacts.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from sceneforge.core.artifact import Artifact
from sceneforge.media.base import Media


@runtime_checkable
class Provider(Protocol):
    """
    Protocol for processing media into artifacts.

    Any class with a run() method returning list[Artifact] participates.
    Implementations don't need to inherit from this protocol.
    """

    def run(self, media: Media) -> list[Artifact[Any]]:
        """Process media and return artifacts."""
        ...
