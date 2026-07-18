"""
SceneForge Whisper Contrib Package

Real implementation of `Capability.TRANSCRIBE` via faster-whisper, with
the model injected rather than constructed internally -- see
`provider.py`'s module docstring for why. This is SceneForge's third
real (non-stub) capability, after frame extraction
(`sceneforge.contrib.ffmpeg`) and scene detection
(`sceneforge.contrib.scenedetect`), and the first one that's genuinely
slow enough (a real speech model, not a subprocess call) to justify
`AsyncPipeline`'s existence in practice.
"""

from sceneforge.contrib.whisper.provider import (
    WhisperModelProtocol,
    WhisperTranscribeProvider,
)
from sceneforge.contrib.whisper.transcript_artifact import TranscriptSegmentArtifact

__all__ = [
    "TranscriptSegmentArtifact",
    "WhisperModelProtocol",
    "WhisperTranscribeProvider",
]
