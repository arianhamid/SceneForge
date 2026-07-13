"""
SceneForge Capability

Defines the capabilities that providers can implement.
"""

from enum import StrEnum


class Capability(StrEnum):
    """
    Capabilities that providers can implement.

    Each capability represents a specific type of processing
    that a provider can perform on artifacts.

    Uses StrEnum for natural serialization:
        capabilities = ["caption", "ocr"]
        {"capability": "caption"}
    """

    CAPTION = "caption"
    TRANSCRIBE = "transcribe"
    DETECT_SCENES = "detect_scenes"
    OCR = "ocr"
    FACE_DETECTION = "face_detection"
    OBJECT_DETECTION = "object_detection"
    AUDIO_ANALYSIS = "audio_analysis"
    EMBEDDING = "embedding"
    FRAME_EXTRACTION = "frame_extraction"
