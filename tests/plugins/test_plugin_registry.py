from collections.abc import Iterable

import pytest

from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import DuplicateProviderError, ProviderNotFoundError
from sceneforge.core.provider import Provider
from sceneforge.plugins.plugin import Plugin
from sceneforge.plugins.registry import PluginRegistry


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

    def process(self, artifacts, *, context=None):
        return artifacts


class DummyPlugin(Plugin):
    @property
    def id(self) -> str:
        return "dummy"

    @property
    def name(self) -> str:
        return "Dummy"

    @property
    def version(self) -> str:
        return "0.1.0"

    @property
    def providers(self) -> Iterable[Provider]:
        return [DummyProvider()]


def test_register_plugin():

    registry = PluginRegistry()

    registry.register(DummyPlugin())

    assert len(registry) == 1


def test_get_plugin():

    registry = PluginRegistry()

    plugin = DummyPlugin()

    registry.register(plugin)

    assert registry.get("dummy") is plugin


def test_register_duplicate_raises():
    registry = PluginRegistry()
    plugin = DummyPlugin()
    registry.register(plugin)
    
    with pytest.raises(DuplicateProviderError):
        registry.register(plugin)


def test_get_nonexistent_raises():
    registry = PluginRegistry()
    
    with pytest.raises(ProviderNotFoundError):
        registry.get("nonexistent")


def test_plugins():
    registry = PluginRegistry()
    plugin = DummyPlugin()
    registry.register(plugin)
    
    plugins = list(registry.plugins())
    assert len(plugins) == 1
    assert plugins[0] is plugin
