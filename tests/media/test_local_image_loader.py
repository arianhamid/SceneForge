from pathlib import Path

import pytest

from sceneforge.media.exceptions import (
    InvalidMediaError,
    MediaNotFoundError,
    UnsupportedMediaError,
)
from sceneforge.media.image import ImageMedia
from sceneforge.media.image_loader import LocalImageLoader

FIXTURES = Path(__file__).parent.parent / "fixtures" / "image"


def test_load_image_returns_image_media():
    loader = LocalImageLoader(FIXTURES / "cat.jpg")
    media = loader.load()

    assert isinstance(media, ImageMedia)
    assert media.name == "cat.jpg"


def test_load_image_has_placeholder_dimensions():
    loader = LocalImageLoader(FIXTURES / "cat.jpg")
    media = loader.load()

    assert media.width == 0
    assert media.height == 0


def test_load_image_has_format():
    loader = LocalImageLoader(FIXTURES / "cat.jpg")
    media = loader.load()

    assert media.fmt == "JPEG"


def test_accepts_string_path():
    loader = LocalImageLoader(str(FIXTURES / "cat.jpg"))
    media = loader.load()

    assert isinstance(media, ImageMedia)


def test_accepts_path_object():
    loader = LocalImageLoader(FIXTURES / "cat.jpg")
    media = loader.load()

    assert isinstance(media, ImageMedia)


def test_missing_file_raises_media_not_found():
    loader = LocalImageLoader(FIXTURES / "missing.jpg")

    with pytest.raises(MediaNotFoundError):
        loader.load()


def test_unsupported_extension_raises():
    loader = LocalImageLoader(FIXTURES / "cat.txt")

    with pytest.raises(UnsupportedMediaError):
        loader.load()


def test_corrupted_image_raises_invalid_media():
    loader = LocalImageLoader(FIXTURES / "corrupted.jpg")

    with pytest.raises(InvalidMediaError):
        loader.load()


def test_media_is_immutable():
    loader = LocalImageLoader(FIXTURES / "cat.jpg")
    media = loader.load()

    with pytest.raises(AttributeError):
        media.name = "changed"  # type: ignore[misc]


def test_media_has_id():
    loader = LocalImageLoader(FIXTURES / "cat.jpg")
    media = loader.load()

    assert media.id is not None
    assert len(str(media.id)) == 36
