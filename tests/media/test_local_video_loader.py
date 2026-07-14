from pathlib import Path

import pytest

from sceneforge.media.exceptions import (
    InvalidMediaError,
    MediaNotFoundError,
    UnsupportedMediaError,
)
from sceneforge.media.video import VideoMedia
from sceneforge.media.video_loader import LocalVideoLoader

FIXTURES = Path(__file__).parent.parent / "fixtures" / "video"


def test_load_video_returns_video_media():
    loader = LocalVideoLoader(FIXTURES / "short.mp4")
    media = loader.load()

    assert isinstance(media, VideoMedia)
    assert media.name == "short.mp4"


def test_load_video_has_format():
    loader = LocalVideoLoader(FIXTURES / "short.mp4")
    media = loader.load()

    assert media.codec == "unknown"  # Will be decoded by providers


def test_accepts_string_path():
    loader = LocalVideoLoader(str(FIXTURES / "short.mp4"))
    media = loader.load()

    assert isinstance(media, VideoMedia)


def test_missing_file_raises_media_not_found():
    loader = LocalVideoLoader(FIXTURES / "missing.mp4")

    with pytest.raises(MediaNotFoundError):
        loader.load()


def test_unsupported_extension_raises():
    loader = LocalVideoLoader(FIXTURES / "video.txt")

    with pytest.raises(UnsupportedMediaError):
        loader.load()


def test_empty_file_raises_invalid_media():
    loader = LocalVideoLoader(FIXTURES / "empty.mp4")

    with pytest.raises(InvalidMediaError):
        loader.load()


def test_media_is_immutable():
    loader = LocalVideoLoader(FIXTURES / "short.mp4")
    media = loader.load()

    with pytest.raises(AttributeError):
        media.name = "changed"  # type: ignore[misc]
