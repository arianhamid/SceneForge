import pytest

from sceneforge.media.image import ImageMedia


def test_image_media_construction():
    image = ImageMedia(name="photo.jpg", width=1920, height=1080, fmt="JPEG")

    assert image.name == "photo.jpg"
    assert image.width == 1920
    assert image.height == 1080
    assert image.fmt == "JPEG"


def test_image_media_is_immutable():
    image = ImageMedia(name="photo.jpg", width=1920, height=1080, fmt="JPEG")

    with pytest.raises(AttributeError):
        image.width = 640  # type: ignore[misc]


def test_image_media_aspect_ratio():
    image = ImageMedia(name="photo.jpg", width=1920, height=1080, fmt="JPEG")

    assert image.aspect_ratio == 16 / 9


def test_image_media_pixel_count():
    image = ImageMedia(name="photo.jpg", width=1920, height=1080, fmt="JPEG")

    assert image.pixel_count == 1920 * 1080


def test_image_media_from_dimensions():
    image = ImageMedia.from_dimensions("photo.jpg", 1920, 1080, "PNG")

    assert image.width == 1920
    assert image.height == 1080
