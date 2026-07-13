from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.provider import Provider
from sceneforge.core.registry import ProviderRegistry


class DummyArtifact(Artifact):
    pass


class DummyProvider(Provider):

    @property
    def name(self):
        return "dummy"

    @property
    def version(self):
        return "1.0.0"

    @property
    def capabilities(self):
        return frozenset({Capability.CAPTION})

    def process(self, artifacts):
        return artifacts


def test_register_provider():

    registry = ProviderRegistry()

    provider = DummyProvider()

    registry.register(provider)

    assert len(registry) == 1


def test_get_provider():

    registry = ProviderRegistry()

    provider = DummyProvider()

    registry.register(provider)

    assert registry.get("dummy") is provider


def test_find_by_capability():

    registry = ProviderRegistry()

    provider = DummyProvider()

    registry.register(provider)

    providers = registry.by_capability(
        Capability.CAPTION
    )

    assert provider in providers