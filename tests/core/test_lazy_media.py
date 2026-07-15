"""Tests for LazyMedia."""

from sceneforge.core.lazy_media import LazyMedia
from sceneforge.media.image import ImageMedia


def test_lazy_media_wraps_media():
    """LazyMedia should wrap media object."""
    image = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")
    lazy = LazyMedia(image)
    
    assert lazy.media is image
    assert lazy.id == image.id


def test_lazy_media_defers_decoding():
    """LazyMedia should defer decoding until requested."""
    image = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")
    lazy = LazyMedia(image)
    
    # Decoding should not happen yet
    assert lazy._decoded is None


def test_lazy_media_decodes_on_demand():
    """LazyMedia should decode when decode() is called."""
    from sceneforge.runtime.media_runtime import StubDecoder
    
    image = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")
    decoder = StubDecoder()
    lazy = LazyMedia(image, decoder)
    
    decoded = lazy.decode()
    
    assert decoded is not None
    assert decoded.media_id == image.id
