from sceneforge.core.exceptions import (
    ProviderError,
    ProviderNotFoundError,
    InvalidMediaError,
)


def test_provider_error_is_base_exception():
    assert issubclass(ProviderError, Exception)


def test_provider_not_found_is_scene_forge_error():
    from sceneforge.core.exceptions import SceneForgeError

    assert issubclass(ProviderNotFoundError, SceneForgeError)


def test_invalid_media_is_provider_error():
    assert issubclass(InvalidMediaError, ProviderError)


def test_provider_not_found_has_name():
    exc = ProviderNotFoundError(name="ocr")
    assert exc.name == "ocr"
    assert "ocr" in str(exc)


def test_invalid_media_has_reason():
    exc = InvalidMediaError(reason="Unsupported format")
    assert exc.reason == "Unsupported format"
