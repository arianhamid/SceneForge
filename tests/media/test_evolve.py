"""Tests for Media.evolve() -- the sanctioned immutable-update path."""

from sceneforge.media.image import ImageMedia
from sceneforge.media.video import VideoMedia


def test_evolve_returns_new_instance():
    original = VideoMedia(name="movie.mp4", duration=0.0, codec="unknown", fps=0.0)
    updated = original.evolve(duration=120.0, codec="h264", fps=24.0)

    assert updated is not original
    assert updated.duration == 120.0
    assert updated.codec == "h264"
    assert updated.fps == 24.0


def test_evolve_preserves_identity_by_default():
    original = VideoMedia(name="movie.mp4", duration=0.0, codec="unknown", fps=0.0)
    updated = original.evolve(duration=120.0)

    # Same logical media, same id -- enrichment corrects facts about
    # the media, it doesn't create a new media.
    assert updated.id == original.id
    assert updated.name == original.name


def test_evolve_does_not_mutate_original():
    original = VideoMedia(name="movie.mp4", duration=0.0, codec="unknown", fps=0.0)
    original.evolve(duration=120.0)

    assert original.duration == 0.0


def test_evolve_merges_metadata_rather_than_replacing():
    original = ImageMedia(
        name="frame.png", width=10, height=10, fmt="PNG", metadata={"source": "loader"}
    )
    updated = original.evolve(metadata={"hash": "abc123"})

    assert updated.metadata["source"] == "loader"
    assert updated.metadata["hash"] == "abc123"


def test_evolve_returns_correct_concrete_type():
    original = ImageMedia(name="frame.png", width=10, height=10, fmt="PNG")
    updated = original.evolve(width=20)

    assert isinstance(updated, ImageMedia)
    assert updated.width == 20
    assert updated.height == 10
