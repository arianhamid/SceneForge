"""
Tests for entry-point based plugin discovery.

Uses unittest.mock to simulate installed entry points rather than
requiring an actual separate package to be pip-installed during CI.
"""

from collections.abc import Iterable
from unittest.mock import MagicMock, patch

from sceneforge.core.capability import Capability
from sceneforge.core.provider import Provider
from sceneforge.plugins.plugin import Plugin
from sceneforge.plugins.registry import (
    PLUGIN_ENTRY_POINT_GROUP,
    PluginRegistry,
    discover_plugins,
)


class DummyProvider(Provider):
    @property
    def name(self) -> str:
        return "dummy"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.CAPTION})

    def run(self, media):
        return []


class DiscoverablePlugin(Plugin):
    @property
    def id(self) -> str:
        return "discoverable"

    @property
    def name(self) -> str:
        return "Discoverable"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def providers(self) -> Iterable[Provider]:
        return [DummyProvider()]


def _fake_entry_point(loadable):
    ep = MagicMock()
    ep.load.return_value = loadable
    return ep


def test_discover_plugins_instantiates_class_entry_points():
    entry_point = _fake_entry_point(DiscoverablePlugin)

    with patch("sceneforge.plugins.registry.entry_points", return_value=[entry_point]):
        plugins = discover_plugins()

    assert len(plugins) == 1
    assert plugins[0].id == "discoverable"


def test_discover_plugins_accepts_instance_entry_points():
    instance = DiscoverablePlugin()
    entry_point = _fake_entry_point(instance)

    with patch("sceneforge.plugins.registry.entry_points", return_value=[entry_point]):
        plugins = discover_plugins()

    assert plugins == [instance]


def test_discover_plugins_skips_broken_entry_points():
    broken = MagicMock()
    broken.load.side_effect = ImportError("missing dependency")
    good = _fake_entry_point(DiscoverablePlugin)

    with patch("sceneforge.plugins.registry.entry_points", return_value=[broken, good]):
        plugins = discover_plugins()

    assert len(plugins) == 1


def test_discover_plugins_skips_non_plugin_objects():
    entry_point = _fake_entry_point(object())

    with patch("sceneforge.plugins.registry.entry_points", return_value=[entry_point]):
        plugins = discover_plugins()

    assert plugins == []


def test_registry_discover_registers_new_plugins():
    registry = PluginRegistry()
    entry_point = _fake_entry_point(DiscoverablePlugin)

    with patch("sceneforge.plugins.registry.entry_points", return_value=[entry_point]):
        newly_registered = registry.discover()

    assert len(newly_registered) == 1
    assert len(registry) == 1
    assert registry.get("discoverable").id == "discoverable"


def test_registry_discover_is_idempotent():
    registry = PluginRegistry()
    entry_point = _fake_entry_point(DiscoverablePlugin)

    with patch("sceneforge.plugins.registry.entry_points", return_value=[entry_point]):
        registry.discover()
        second_pass = registry.discover()

    # Calling discover() again must not raise DuplicateProviderError,
    # and must not double-register.
    assert second_pass == []
    assert len(registry) == 1


def test_default_entry_point_group_name():
    assert PLUGIN_ENTRY_POINT_GROUP == "sceneforge.plugins"
