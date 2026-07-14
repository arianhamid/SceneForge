from sceneforge.media.base import Media
from sceneforge.media.loader import MediaLoader


def test_media_loader_is_protocol() -> None:
    assert hasattr(MediaLoader, "__protocol_attrs__")


def test_media_loader_has_load_method() -> None:
    assert hasattr(MediaLoader, "load")


def test_media_loader_is_abstract() -> None:
    # Protocol classes are not directly instantiable
    try:
        MediaLoader()
        raise AssertionError("MediaLoader should not be instantiable")
    except TypeError:
        pass


def test_runtime_checkable() -> None:
    class ConcreteLoader:
        def load(self) -> Media:
            return Media(name="test")

    assert isinstance(ConcreteLoader(), MediaLoader)
