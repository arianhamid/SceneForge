from sceneforge.media import (
    AudioMedia,
    ImageMedia,
    LocalAudioLoader,
    LocalImageLoader,
    LocalVideoLoader,
    Media,
    MediaLoader,
    VideoMedia,
)


def test_all_media_types_exported():
    assert Media is not None
    assert ImageMedia is not None
    assert VideoMedia is not None
    assert AudioMedia is not None


def test_all_loaders_exported():
    assert MediaLoader is not None
    assert LocalImageLoader is not None
    assert LocalVideoLoader is not None
    assert LocalAudioLoader is not None
