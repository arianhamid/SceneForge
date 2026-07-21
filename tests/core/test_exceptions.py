"""Tests for SceneForge exceptions."""

from sceneforge.core.exceptions import IncompatibleMediaError


def test_incompatible_media_error():
    """IncompatibleMediaError should contain provider and media info."""
    error = IncompatibleMediaError(
        provider="image_caption", media_type="AudioMedia", capabilities={"caption"}
    )
    assert error.provider == "image_caption"
    assert error.media_type == "AudioMedia"
    assert error.capabilities == {"caption"}
    assert "image_caption" in str(error)
    assert "AudioMedia" in str(error)
