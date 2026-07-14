"""Tests for capability registry."""

from sceneforge.core.capability import Capability
from sceneforge.core.capability_registry import register_default_capabilities
from sceneforge.media.image import ImageMedia
from sceneforge.media.audio import AudioMedia
from sceneforge.media.video import VideoMedia


def test_register_default_capabilities():
    """Default capabilities should be registered."""
    register_default_capabilities()
    
    # Import to verify registration
    from sceneforge.core.pipeline import _CAPABILITY_MEDIA_MAP
    
    assert ImageMedia in _CAPABILITY_MEDIA_MAP[Capability.CAPTION]
    assert AudioMedia in _CAPABILITY_MEDIA_MAP[Capability.TRANSCRIBE]
    assert VideoMedia in _CAPABILITY_MEDIA_MAP[Capability.DETECT_SCENES]