from uuid import UUID

import pytest

from sceneforge.media.base import Media


def test_media_has_uuid():
    media = Media(name="test")

    assert isinstance(media.id, UUID)


def test_media_has_name():
    media = Media(name="video.mp4")

    assert media.name == "video.mp4"


def test_media_is_immutable():
    media = Media(name="test")

    with pytest.raises(AttributeError):
        media.name = "changed"  # type: ignore[misc]


def test_media_metadata_is_immutable():
    media = Media(name="test", metadata={"key": "value"})

    with pytest.raises(TypeError):
        media.metadata["new_key"] = "new_value"  # type: ignore[index]


def test_media_default_metadata():
    media = Media(name="test")

    assert media.metadata == {}
