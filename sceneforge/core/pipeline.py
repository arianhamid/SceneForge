from __future__ import annotations

from typing import Any

from sceneforge.core.artifact import Artifact
from sceneforge.core.provider_protocol import Provider
from sceneforge.media.base import Media


class Pipeline:
    """
    The orchestration boundary for SceneForge.

    Pipeline is the single entry point for processing media through providers.
    It owns the workflow: Media -> Provider -> Artifacts.

    Phase 1.5: Single-provider design. Provider composition (chaining)
    will be added in Phase 5.

    Example:
        pipeline = Pipeline(provider=IdentityProvider())
        artifacts = pipeline.run(media)
    """

    def __init__(self, provider: Provider) -> None:
        """
        Initialize Pipeline with a single provider.

        Args:
            provider: The provider to use for processing.
        """
        self._provider = provider

    def run(self, media: Media) -> list[Artifact[Any]]:
        """
        Process media through the provider and return artifacts.

        Args:
            media: The media object to process.

        Returns:
            A list of artifacts produced by the provider.
        """
        return self._provider.run(media)
