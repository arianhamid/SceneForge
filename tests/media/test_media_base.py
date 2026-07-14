from uuid import UUID
from sceneforge.media.base import Media


def test_media_has_uuid():
    media = Media(name="test")

    assert isinstance(media.id, UUID)


def test_media_has_name():
    media = Media(name="video.mp4")

    assert media.name == "video.mp4"


def test_media_is_immutable():
    media = Media(name="test")

    try:
        media.name = "changed"  # type: ignore[misc]
        assert False, "Media should be immutable"
    except AttributeError:
        pass


def test_media_metadata_is_immutable():
    media = Media(name="test", metadata={"key": "value"})

    try:
        media.metadata["new_key"] = "new_value"  # type: ignore[index]
        assert False, "Metadata should be immutable"
    except TypeError:
        pass


def test_media_default_metadata():
    media = Media(name="test")

    assert media.metadata == {}
