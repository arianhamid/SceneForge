"""
SceneForge Provider

Base class for all providers that interact with external AI systems.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability

if TYPE_CHECKING:
    from sceneforge.media.base import Media


class Provider(ABC):
    """
    Abstract base class for all SceneForge providers.

    Providers communicate with external AI systems and produce
    artifacts. They should never contain knowledge construction
    or application logic.

    The run() method is the contract: accept Media, return list[Artifact].
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the provider version."""

    @property
    @abstractmethod
    def capabilities(self) -> frozenset[Capability]:
        """Return the capabilities this provider implements."""

    @abstractmethod
    def run(self, media: Media) -> list[Artifact[Any]]:
        """Process media and return artifacts."""
