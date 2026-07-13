"""
Plugin registry.
"""

from __future__ import annotations

from collections.abc import Iterable

from sceneforge.core.exceptions import (
    DuplicateProviderError,
    ProviderNotFoundError,
)
from sceneforge.plugins.plugin import Plugin


class PluginRegistry:
    """
    Stores installed plugins.
    """

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}

    def register(self, plugin: Plugin) -> None:
        if plugin.id in self._plugins:
            raise DuplicateProviderError(plugin.id)

        self._plugins[plugin.id] = plugin

    def get(self, plugin_id: str) -> Plugin:
        if plugin_id not in self._plugins:
            raise ProviderNotFoundError(plugin_id)

        return self._plugins[plugin_id]

    def plugins(self) -> Iterable[Plugin]:
        return self._plugins.values()

    def __len__(self) -> int:
        return len(self._plugins)
