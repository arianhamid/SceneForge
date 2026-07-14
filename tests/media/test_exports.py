from sceneforge.media import AudioMedia, ImageMedia, Media, VideoMedia


def test_all_media_types_exported():
    assert Media is not None
    assert ImageMedia is not None
    assert VideoMedia is not None
    assert AudioMedia is not None
