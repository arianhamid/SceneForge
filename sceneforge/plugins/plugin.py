"""
SceneForge Plugin Interface.

A plugin groups one or more providers and exposes them to the
framework.

Plugins contain metadata only.
They never perform processing directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from sceneforge.core.provider import Provider


class Plugin(ABC):
    """
    Base interface for SceneForge plugins.
    """

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique plugin identifier."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable plugin name."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""

    @property
    @abstractmethod
    def providers(self) -> Iterable[Provider]:
        """Providers exposed by this plugin."""
