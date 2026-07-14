from sceneforge.media.base import Media
from sceneforge.core.artifact import Artifact
from sceneforge.core.provider_protocol import Provider


def test_provider_is_protocol():
    assert hasattr(Provider, "__protocol_attrs__")


def test_provider_has_run_method():
    assert hasattr(Provider, "run")


def test_provider_is_abstract():
    try:
        Provider()
        assert False, "Provider should not be instantiable"
    except TypeError:
        pass


def test_runtime_checkable():
    class ConcreteProvider:
        def run(self, media: Media) -> list[Artifact]:
            return []

    assert isinstance(ConcreteProvider(), Provider)
