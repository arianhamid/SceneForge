"""
SceneForge Capability Registry

Registers which media types each capability supports.
"""

from sceneforge.core.capability import Capability
from sceneforge.media.base import Media


def register_default_capabilities() -> None:
    """Register default capability-to-media mappings."""
    from sceneforge.core.pipeline import register_capability_media
    from sceneforge.media.image import ImageMedia
    from sceneforge.media.video import VideoMedia
    from sceneforge.media.audio import AudioMedia
    
    # Image/Video capabilities
    register_capability_media(Capability.CAPTION, {ImageMedia, VideoMedia})
    register_capability_media(Capability.OCR, {ImageMedia, VideoMedia})
    register_capability_media(Capability.FACE_DETECTION, {ImageMedia, VideoMedia})
    register_capability_media(Capability.OBJECT_DETECTION, {ImageMedia, VideoMedia})
    register_capability_media(Capability.EMBEDDING, {ImageMedia, VideoMedia, AudioMedia})
    
    # Video-only capabilities
    register_capability_media(Capability.DETECT_SCENES, {VideoMedia})
    register_capability_media(Capability.FRAME_EXTRACTION, {VideoMedia})
    
    # Audio capabilities
    register_capability_media(Capability.TRANSCRIBE, {AudioMedia, VideoMedia})
    register_capability_media(Capability.AUDIO_ANALYSIS, {AudioMedia})