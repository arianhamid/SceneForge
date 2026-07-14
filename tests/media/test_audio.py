import pytest

from sceneforge.media.audio import AudioMedia


def test_audio_media_construction():
    audio = AudioMedia(
        name="sound.wav",
        duration=30.0,
        sample_rate=44100,
        channels=2,
    )

    assert audio.name == "sound.wav"
    assert audio.duration == 30.0
    assert audio.sample_rate == 44100
    assert audio.channels == 2


def test_audio_media_is_immutable():
    audio = AudioMedia(name="sound.wav", duration=30.0, sample_rate=44100, channels=2)

    with pytest.raises(AttributeError):
        audio.duration = 0.0  # type: ignore[misc]


def test_audio_media_from_file():
    audio = AudioMedia.from_file(
        "sound.wav", duration=30.0, sample_rate=44100, channels=2
    )

    assert audio.name == "sound.wav"


def test_audio_media_bit_depth():
    audio = AudioMedia(name="sound.wav", duration=30.0, sample_rate=44100, channels=2)

    # Default bit depth is 16
    assert audio.bit_depth == 16
