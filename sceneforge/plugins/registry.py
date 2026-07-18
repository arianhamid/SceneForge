"""
Plugin registry.

PluginRegistry used to only support manual `.register(plugin)` calls,
which meant installing a third-party plugin package still required
editing the host application's bootstrap code -- directly
contradicting PLUGIN_SPEC.md's promise that "plugins should require
zero modifications to the core framework."

`discover_plugins()` / `PluginRegistry.discover()` close that gap
using the standard `importlib.metadata.entry_points()` mechanism: a
plugin package declares itself once in its own `pyproject.toml`

    [project.entry-points."sceneforge.plugins"]
    my_plugin = "my_package.plugin:MyPlugin"

and any host application picks it up automatically just by having the
package installed -- no import, no manual registration call.
"""

from __future__ import annotations

from collections.abc import Iterable
from importlib.metadata import entry_points

from sceneforge.core.exceptions import (
    DuplicateProviderError,
    ProviderNotFoundError,
)
from sceneforge.plugins.plugin import Plugin

#: The entry-point group SceneForge plugins declare themselves under.
PLUGIN_ENTRY_POINT_GROUP = "sceneforge.plugins"


def discover_plugins(group: str = PLUGIN_ENTRY_POINT_GROUP) -> list[Plugin]:
    """
    Instantiate every Plugin registered under ``group`` via entry points.

    Broken entry points (an uninstalled dependency, an import error in
    a third-party package) are skipped rather than raised, since one
    bad plugin package should not prevent the host application from
    starting. Discovery is a best-effort convenience, not a
    correctness-critical path.
    """
    plugins: list[Plugin] = []
    for entry_point in entry_points(group=group):
        try:
            plugin_cls = entry_point.load()
            plugin = plugin_cls() if isinstance(plugin_cls, type) else plugin_cls
        except Exception:  # noqa: BLE001 - a broken plugin must not break discovery
            continue
        if isinstance(plugin, Plugin):
            plugins.append(plugin)
    return plugins


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

    def discover(self, group: str = PLUGIN_ENTRY_POINT_GROUP) -> list[Plugin]:
        """
        Find and register every Plugin declared via entry points under
        ``group``. Plugins already registered (by id) are left as-is
        rather than raising -- discovery is meant to be safe to call
        repeatedly (e.g. once per host application startup).

        Returns the list of newly-registered plugins.
        """
        newly_registered: list[Plugin] = []
        for plugin in discover_plugins(group=group):
            if plugin.id in self._plugins:
                continue
            self._plugins[plugin.id] = plugin
            newly_registered.append(plugin)
        return newly_registered

    def get(self, plugin_id: str) -> Plugin:
        if plugin_id not in self._plugins:
            raise ProviderNotFoundError(plugin_id)

        return self._plugins[plugin_id]

    def plugins(self) -> Iterable[Plugin]:
        return self._plugins.values()

    def __len__(self) -> int:
        return len(self._plugins)
