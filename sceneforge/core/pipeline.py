from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from sceneforge.core.artifact import Artifact

if TYPE_CHECKING:
    from sceneforge.media.base import Media
    from sceneforge.runtime import ProcessingContext


class Pipeline:
    """
    The orchestration boundary for SceneForge.

    Pipeline is the single entry point for processing media through providers.
    It owns the workflow: Media -> Provider -> Artifacts.

    Example:
        pipeline = Pipeline(provider=IdentityProvider())
        artifacts = pipeline.run(media)
    """

    def __init__(self, provider: object) -> None:
        """
        Initialize Pipeline with a single provider.

        Args:
            provider: The provider to use for processing.
        """
        self._provider = provider

    def run(
        self,
        media: Media,
        *,
        context: ProcessingContext | None = None,
    ) -> Iterable[Artifact]:
        """
        Process media through the provider and return artifacts.

        Args:
            media: The media object to process.
            context: Optional processing context for state management.

        Returns:
            An iterable of artifacts produced by the provider.
        """
        return self._provider.run(media)
