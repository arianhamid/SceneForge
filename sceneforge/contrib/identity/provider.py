"""
Identity Provider.

Returns artifacts unchanged. Useful for:
- Testing pipeline architecture
- Benchmarking overhead
- Validating framework correctness
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.provider import Provider

if TYPE_CHECKING:
    from sceneforge.runtime.processing_context import ProcessingContext


class IdentityProvider(Provider):
    """
    Provider that returns artifacts unchanged.

    This is the simplest possible provider, useful for
    validating the architecture without any dependencies.
    """

    @property
    def name(self) -> str:
        return "identity"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset()

    def process(
        self,
        artifacts: Iterable[Artifact],  # type: ignore[type-arg]
        *,
        context: ProcessingContext | None = None,
    ) -> Iterable[Artifact]:  # type: ignore[type-arg]
        return artifacts
