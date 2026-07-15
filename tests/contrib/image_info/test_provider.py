"""Tests for ImageInfoProvider."""

from sceneforge.contrib.image_info import ImageInfoProvider
from sceneforge.contrib.image_info.artifacts import ImageInfoArtifact
from sceneforge.media.image import ImageMedia
from tests.contracts.provider_contract import provider_contract


def test_image_info_provider_name():
    """ImageInfoProvider should have correct name."""
    provider = ImageInfoProvider()
    assert provider.name == "image_info"


def test_image_info_provider_version():
    """ImageInfoProvider should have correct version."""
    provider = ImageInfoProvider()
    assert provider.version == "1.0.0"


def test_image_info_provider_returns_artifact():
    """ImageInfoProvider should return ImageInfoArtifact."""
    provider = ImageInfoProvider()
    image = ImageMedia(name="test.jpg", width=1920, height=1080, fmt="JPEG")

    artifacts = provider.run(image)

    assert len(artifacts) == 1
    assert isinstance(artifacts[0], ImageInfoArtifact)


def test_image_info_provider_extracts_metadata():
    """ImageInfoProvider should extract correct metadata."""
    provider = ImageInfoProvider()
    image = ImageMedia(name="test.jpg", width=1920, height=1080, fmt="JPEG")

    artifacts = provider.run(image)
    artifact = artifacts[0]

    assert artifact.media_id == image.id
    assert artifact.width == 1920
    assert artifact.height == 1080
    assert artifact.aspect_ratio == 1920 / 1080
    assert artifact.pixel_count == 1920 * 1080
    assert artifact.fmt == "JPEG"


def test_image_info_provider_rejects_non_image():
    """ImageInfoProvider should reject non-image media."""
    import pytest

    from sceneforge.media.audio import AudioMedia

    provider = ImageInfoProvider()
    audio = AudioMedia(
        name="sound.wav",
        duration=30.0,
        sample_rate=44100,
        channels=2,
    )

    with pytest.raises(TypeError) as exc_info:
        provider.run(audio)

    assert "Expected ImageMedia" in str(exc_info.value)


def test_image_info_provider_capabilities():
    """ImageInfoProvider should have empty capabilities."""
    provider = ImageInfoProvider()
    assert provider.capabilities == frozenset()


def test_image_info_provider_satisfies_contract():
    """ImageInfoProvider should satisfy provider contract."""
    provider = ImageInfoProvider()
    image = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")

    # Should not raise
    provider_contract(provider, image)
