"""
MediaHash Provider Tests.
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

from sceneforge.contrib.media_hash import MediaHashArtifact, MediaHashProvider
from sceneforge.media.image import ImageMedia


def test_media_hash_provider_name():
    provider = MediaHashProvider()
    assert provider.name == "media_hash"


def test_media_hash_provider_version():
    provider = MediaHashProvider()
    assert provider.version == "1.0.0"


def test_media_hash_provider_returns_media_hash_artifact():
    provider = MediaHashProvider()
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")

    result = provider.run(media)

    assert len(result) == 1
    assert isinstance(result[0], MediaHashArtifact)
    assert result[0].provider == "media_hash"


def test_media_hash_preserves_media_id():
    provider = MediaHashProvider()
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")

    result = provider.run(media)

    assert result[0].media_id == media.id


def test_media_hash_deterministic():
    """Same input produces same hash."""
    provider = MediaHashProvider()
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")

    result1 = provider.run(media)
    result2 = provider.run(media)

    assert result1[0].hash_value == result2[0].hash_value


def test_media_hash_different_inputs_different_hashes():
    """Different media names produce different hashes."""
    provider = MediaHashProvider()
    media1 = ImageMedia(name="test1.jpg", width=100, height=100, fmt="JPEG")
    media2 = ImageMedia(name="test2.jpg", width=100, height=100, fmt="JPEG")

    result1 = provider.run(media1)
    result2 = provider.run(media2)

    assert result1[0].hash_value != result2[0].hash_value


def test_media_hash_source_type_identity():
    """When no source path, uses identity hash based on name."""
    provider = MediaHashProvider()
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")

    result = provider.run(media)

    assert result[0].source_type == "identity"
    assert result[0].algorithm == "sha256"


def test_media_hash_source_type_file():
    """When source path exists in metadata, hashes file content."""
    provider = MediaHashProvider()

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"hello world")
        source_path = f.name

    try:
        media = ImageMedia(
            name="test.jpg",
            width=100,
            height=100,
            fmt="JPEG",
            metadata={"source": source_path},
        )

        result = provider.run(media)

        assert result[0].source_type == "file"
        assert result[0].algorithm == "sha256"

        expected_hash = hashlib.sha256(b"hello world").hexdigest()
        assert result[0].hash_value == expected_hash
    finally:
        Path(source_path).unlink(missing_ok=True)


def test_media_hash_identity_uses_name():
    """Identity hash is based on name, not UUID."""
    provider = MediaHashProvider()
    media1 = ImageMedia(name="same_name.jpg", width=100, height=100, fmt="JPEG")
    media2 = ImageMedia(name="same_name.jpg", width=200, height=200, fmt="PNG")

    result1 = provider.run(media1)
    result2 = provider.run(media2)

    assert result1[0].hash_value == result2[0].hash_value
    assert result1[0].media_id != result2[0].media_id
