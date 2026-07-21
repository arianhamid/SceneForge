from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.provider import Provider
from sceneforge.media.base import Media


class DummyArtifact(Artifact):
    pass


class DummyProvider(Provider):
    @property
    def name(self) -> str:
        return "dummy"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def capabilities(self):
        return frozenset({Capability.CAPTION})

    def run(self, media: Media):
        return [DummyArtifact(provider=self.name)]


def test_provider_properties():

    provider = DummyProvider()

    assert provider.name == "dummy"

    assert provider.version == "1.0"

    assert Capability.CAPTION in provider.capabilities
