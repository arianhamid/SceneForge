from collections.abc import Iterable

from sceneforge.core.provider import Provider
from sceneforge.plugins.plugin import Plugin
from sceneforge.plugins.registry import PluginRegistry


class DummyProvider(Provider):
    @property
    def metadata(self):
        raise NotImplementedError

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
