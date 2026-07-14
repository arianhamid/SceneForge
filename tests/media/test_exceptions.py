from sceneforge.media.exceptions import (
    InvalidMediaError,
    MediaError,
    MediaIOError,
    MediaNotFoundError,
    UnsupportedMediaError,
)


def test_media_error_is_base_exception():
    assert issubclass(MediaError, Exception)


def test_media_not_found_is_media_error():
    assert issubclass(MediaNotFoundError, MediaError)


def test_unsupported_media_is_media_error():
    assert issubclass(UnsupportedMediaError, MediaError)


def test_invalid_media_is_media_error():
    assert issubclass(InvalidMediaError, MediaError)


def test_media_io_is_media_error():
    assert issubclass(MediaIOError, MediaError)


def test_media_not_found_has_path():
    exc = MediaNotFoundError(path="/missing.jpg")
    assert exc.path == "/missing.jpg"
    assert "missing.jpg" in str(exc)


def test_unsupported_media_has_extension():
    exc = UnsupportedMediaError(extension=".psd", loader="LocalImageLoader")
    assert exc.extension == ".psd"
    assert exc.loader == "LocalImageLoader"


def test_invalid_media_has_path():
    exc = InvalidMediaError(path="/corrupted.jpg", reason="Invalid JPEG data")
    assert exc.path == "/corrupted.jpg"
    assert exc.reason == "Invalid JPEG data"


def test_media_io_has_path():
    original = PermissionError("denied")
    exc = MediaIOError(path="/locked.jpg", original=original)
    assert exc.path == "/locked.jpg"
    assert exc.__cause__ is original
