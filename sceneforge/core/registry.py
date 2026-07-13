"""
SceneForge Provider Registry.

Keeps track of available providers and allows discovery
by name or capability.
"""

from __future__ import annotations

from collections.abc import Iterable

from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import (
    DuplicateProviderError,
    ProviderNotFoundError,
)
from sceneforge.core.provider import Provider


class Registry:
    """
    Registry of available providers.

    The registry owns provider instances and exposes simple
    discovery APIs.
    """

    def __init__(self) -> None:
        self._providers: dict[str, Provider] = {}

    def register(self, provider: Provider) -> None:
        """Register a provider."""

        if provider.name in self._providers:
            raise DuplicateProviderError(provider.name)

        self._providers[provider.name] = provider

    def unregister(self, name: str) -> None:
        """Remove a provider."""

        if name not in self._providers:
            raise ProviderNotFoundError(name)

        self._providers.pop(name)

    def get(self, name: str) -> Provider:
        """Return a provider by name."""

        if name not in self._providers:
            raise ProviderNotFoundError(name)

        return self._providers[name]

    def providers(self) -> tuple[Provider, ...]:
        """Return all registered providers."""

        return tuple(self._providers.values())

    def by_capability(
        self,
        capability: Capability,
    ) -> tuple[Provider, ...]:
        """Return providers supporting a capability."""

        return tuple(
            provider
            for provider in self._providers.values()
            if capability in provider.capabilities
        )

    def __contains__(self, name: str) -> bool:
        return name in self._providers

    def __len__(self) -> int:
        return len(self._providers)
