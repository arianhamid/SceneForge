from typing import Protocol

from sceneforge.media.loader import MediaLoader
from sceneforge.media.base import Media


def test_media_loader_is_protocol():
    assert hasattr(MediaLoader, "__protocol_attrs__")


def test_media_loader_has_load_method():
    assert hasattr(MediaLoader, "load")


def test_media_loader_is_abstract():
    # Protocol classes are not directly instantiable
    try:
        MediaLoader()
        assert False, "MediaLoader should not be instantiable"
    except TypeError:
        pass
