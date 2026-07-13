"""
SceneForge Provider

Base class for all providers that interact with external AI systems.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import TYPE_CHECKING

from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability

if TYPE_CHECKING:
    from sceneforge.runtime.processing_context import ProcessingContext


class Provider(ABC):
    """
    Abstract base class for all SceneForge providers.

    Providers communicate with external AI systems and produce
    artifacts. They should never contain knowledge construction
    or application logic.
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
    def process(
        self,
        artifacts: Iterable[Artifact],  # type: ignore[type-arg]
        *,
        context: ProcessingContext | None = None,
    ) -> Iterable[Artifact]:  # type: ignore[type-arg]
        """Process artifacts and return new artifacts."""
