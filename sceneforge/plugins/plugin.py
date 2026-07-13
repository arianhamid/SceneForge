"""
SceneForge plugin interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from sceneforge.core.provider import Provider


class Plugin(ABC):
    """
    Base class for all SceneForge plugins.
    """

    @property
    @abstractmethod
    def id(self) -> str: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @property
    @abstractmethod
    def providers(self) -> Iterable[Provider]: ...
