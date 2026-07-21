"""Tests for AudioInfoProvider."""

import pytest

from sceneforge.contrib.audio_info import AudioInfoProvider
from sceneforge.contrib.audio_info.artifacts import AudioInfoArtifact
from sceneforge.media.audio import AudioMedia
from tests.contracts.provider_contract import provider_contract


def test_audio_info_provider_name():
    """AudioInfoProvider should have correct name."""
    provider = AudioInfoProvider()
    assert provider.name == "audio_info"


def test_audio_info_provider_version():
    """AudioInfoProvider should have correct version."""
    provider = AudioInfoProvider()
    assert provider.version == "1.0.0"


def test_audio_info_provider_returns_artifact():
    """AudioInfoProvider should return AudioInfoArtifact."""
    provider = AudioInfoProvider()
    audio = AudioMedia(name="sound.wav", duration=30.0, sample_rate=44100, channels=2)

    artifacts = provider.run(audio)

    assert len(artifacts) == 1
    assert isinstance(artifacts[0], AudioInfoArtifact)


def test_audio_info_provider_extracts_metadata():
    """AudioInfoProvider should extract correct metadata."""
    provider = AudioInfoProvider()
    audio = AudioMedia(
        name="sound.wav", duration=30.0, sample_rate=44100, channels=2, bit_depth=16
    )

    artifacts = provider.run(audio)
    artifact = artifacts[0]

    assert artifact.media_id == audio.id
    assert artifact.duration == 30.0
    assert artifact.sample_rate == 44100
    assert artifact.channels == 2
    assert artifact.bit_depth == 16


def test_audio_info_provider_rejects_non_audio():
    """AudioInfoProvider should reject non-audio media."""
    from sceneforge.media.image import ImageMedia

    provider = AudioInfoProvider()
    image = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")

    with pytest.raises(TypeError) as exc_info:
        provider.run(image)

    assert "Expected AudioMedia" in str(exc_info.value)


def test_audio_info_provider_capabilities():
    """AudioInfoProvider should have empty capabilities."""
    provider = AudioInfoProvider()
    assert provider.capabilities == frozenset()


def test_audio_info_provider_satisfies_contract():
    """AudioInfoProvider should satisfy provider contract."""
    provider = AudioInfoProvider()
    audio = AudioMedia(name="sound.wav", duration=30.0, sample_rate=44100, channels=2)

    # Should not raise
    provider_contract(provider, audio)
