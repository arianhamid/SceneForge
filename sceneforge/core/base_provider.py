"""
SceneForge Base Provider.

Provides common functionality shared by all providers.
"""

from __future__ import annotations

from abc import ABC
from collections.abc import Iterable

from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.provider import Provider
from sceneforge.runtime import ProcessingContext


class BaseProvider(Provider, ABC):
    """
    Convenience base class for providers.

    Subclasses typically only implement `process()`.
    """

    name: str = ""

    version: str = "0.1.0"

    description: str = ""

    capabilities: frozenset[Capability] = frozenset()

    def process(
        self,
        artifacts: Iterable[Artifact],
        *,
        context: ProcessingContext | None = None,
    ) -> Iterable[Artifact]:
        raise NotImplementedError
