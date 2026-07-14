from pathlib import Path

import pytest

from sceneforge.media.audio import AudioMedia
from sceneforge.media.audio_loader import LocalAudioLoader
from sceneforge.media.exceptions import (
    InvalidMediaError,
    MediaNotFoundError,
    UnsupportedMediaError,
)

FIXTURES = Path(__file__).parent.parent / "fixtures" / "audio"


def test_load_audio_returns_audio_media():
    loader = LocalAudioLoader(FIXTURES / "beep.wav")
    media = loader.load()

    assert isinstance(media, AudioMedia)
    assert media.name == "beep.wav"


def test_load_audio_has_defaults():
    loader = LocalAudioLoader(FIXTURES / "beep.wav")
    media = loader.load()

    assert media.sample_rate == 0  # Will be decoded by providers
    assert media.channels == 0  # Will be decoded by providers


def test_accepts_string_path():
    loader = LocalAudioLoader(str(FIXTURES / "beep.wav"))
    media = loader.load()

    assert isinstance(media, AudioMedia)


def test_missing_file_raises_media_not_found():
    loader = LocalAudioLoader(FIXTURES / "missing.wav")

    with pytest.raises(MediaNotFoundError):
        loader.load()


def test_unsupported_extension_raises():
    loader = LocalAudioLoader(FIXTURES / "audio.txt")

    with pytest.raises(UnsupportedMediaError):
        loader.load()


def test_empty_file_raises_invalid_media():
    loader = LocalAudioLoader(FIXTURES / "empty.wav")

    with pytest.raises(InvalidMediaError):
        loader.load()


def test_media_is_immutable():
    loader = LocalAudioLoader(FIXTURES / "beep.wav")
    media = loader.load()

    with pytest.raises(AttributeError):
        media.name = "changed"  # type: ignore[misc]
