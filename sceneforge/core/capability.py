"""
SceneForge Capability

Defines the capabilities that providers can implement.
"""

from enum import Enum, auto


class Capability(Enum):
    """
    Capabilities that providers can implement.

    Each capability represents a specific type of processing
    that a provider can perform on artifacts.
    """

    CAPTION = auto()
    TRANSCRIBE = auto()
    DETECT_SCENES = auto()
    OCR = auto()
    FACE_DETECTION = auto()
    OBJECT_DETECTION = auto()
    AUDIO_ANALYSIS = auto()
    EMBEDDING = auto()
