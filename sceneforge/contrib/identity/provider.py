"""
Identity Provider.

Returns artifacts unchanged. Useful for:
- Testing pipeline architecture
- Benchmarking overhead
- Validating framework correctness
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.identity_artifact import IdentityArtifact
from sceneforge.core.provider import Provider
from sceneforge.media.base import Media

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

    def run(self, media: Media) -> list[Artifact[Any]]:
        """Process media and return artifacts."""
        return [
            IdentityArtifact(
                media_id=media.id,
                provider=self.name,
            )
        ]

    def process(
        self,
        artifacts: Iterable[Artifact],  # type: ignore[type-arg]
        *,
        context: ProcessingContext | None = None,
    ) -> Iterable[Artifact]:  # type: ignore[type-arg]
        return artifacts
