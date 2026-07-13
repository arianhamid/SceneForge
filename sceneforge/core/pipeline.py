"""
SceneForge Pipeline interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from sceneforge.core.artifact import Artifact
from sceneforge.core.provider import Provider
from sceneforge.runtime.processing_context import ProcessingContext


class Pipeline(ABC):
    """
    A Pipeline orchestrates Providers.

    Pipelines do not perform work directly.
    """

    @property
    @abstractmethod
    def providers(self) -> tuple[Provider, ...]: ...

    @abstractmethod
    def run(
        self,
        artifacts: Iterable[Artifact],
        *,
        context: ProcessingContext | None = None,
    ) -> Iterable[Artifact]: ...
