from __future__ import annotations

from typing import Any

from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import IncompatibleMediaError
from sceneforge.core.provider_protocol import Provider
from sceneforge.media.base import Media


# Capability-to-Media mapping
_CAPABILITY_MEDIA_MAP: dict[Capability, set[type[Media]]] = {}


def register_capability_media(
    capability: Capability,
    media_types: set[type[Media]],
) -> None:
    """Register which media types a capability supports."""
    _CAPABILITY_MEDIA_MAP[capability] = media_types


class Pipeline:
    """
    The orchestration boundary for SceneForge.

    Pipeline is the single entry point for processing media through providers.
    It owns the workflow: Media -> Provider -> Artifacts.

    Phase 2: Pipeline validates capabilities before execution.

    Example:
        pipeline = Pipeline(provider=IdentityProvider())
        artifacts = pipeline.run(media)
    """

    _capabilities_registered = False

    def __init__(self, provider: Provider) -> None:
        """
        Initialize Pipeline with a single provider.

        Args:
            provider: The provider to use for processing.
        """
        if not Pipeline._capabilities_registered:
            from sceneforge.core.capability_registry import register_default_capabilities
            register_default_capabilities()
            Pipeline._capabilities_registered = True
        
        self._provider = provider

    def _validate_media(self, media: Media) -> None:
        """
        Validate that media is compatible with provider capabilities.

        Args:
            media: The media object to validate.

        Raises:
            IncompatibleMediaError: If media is incompatible with capabilities.
        """
        capabilities = self._provider.capabilities
        
        # If provider has no capabilities, accept all media
        if not capabilities:
            return
        
        media_type = type(media)
        
        for capability in capabilities:
            supported_types = _CAPABILITY_MEDIA_MAP.get(capability, set())
            
            # If capability has no registered types, skip validation
            if not supported_types:
                continue
            
            if media_type not in supported_types:
                raise IncompatibleMediaError(
                    provider=self._provider.name,
                    media_type=media_type.__name__,
                    capabilities={cap.value for cap in capabilities},
                )

    def run(self, media: Media) -> list[Artifact[Any]]:
        """
        Process media through the provider and return artifacts.

        Args:
            media: The media object to process.

        Returns:
            A list of artifacts produced by the provider.

        Raises:
            IncompatibleMediaError: If media is incompatible with capabilities.
        """
        self._validate_media(media)
        return self._provider.run(media)
