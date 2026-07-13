"""
Identity Provider.

Returns artifacts unchanged. Useful for:
- Testing pipeline architecture
- Benchmarking overhead
- Validating framework correctness
"""

from __future__ import annotations

from collections.abc import Iterable

from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.provider import Provider


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
        artifacts: Iterable[Artifact],
        *,
        context=None,
    ) -> Iterable[Artifact]:
        return artifacts
