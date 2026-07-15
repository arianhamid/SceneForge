"""Tests for decoder protocol."""

from sceneforge.runtime.media_runtime import Decoder


def test_decoder_is_protocol():
    """Decoder should be a Protocol."""
    assert hasattr(Decoder, 'decode')


def test_decoder_is_runtime_checkable():
    """Decoder should be runtime_checkable."""
    from sceneforge.media.image import ImageMedia
    
    class MockDecoder:
        def decode(self, media):
            return None
    
    # Should not raise TypeError
    assert isinstance(MockDecoder(), Decoder)