"""
SceneForge FFmpeg Contrib Package

The framework's first real, non-stub integration: a MediaEnricher
that probes actual video files with `ffprobe`, and a Provider that
extracts actual frames with `ffmpeg`. Everything else shipped in
`sceneforge.contrib` before this returned placeholder/identity data;
this package exists to prove the Media -> Provider -> Artifact
contract holds up against a real external tool, not just mocks.
"""

from sceneforge.contrib.ffmpeg.frame_extraction_artifact import FrameExtractionArtifact
from sceneforge.contrib.ffmpeg.frame_extraction_provider import (
    FFmpegBinaryMissingError,
    FFmpegFrameExtractionProvider,
)
from sceneforge.contrib.ffmpeg.probe_enricher import (
    FFprobeEnricher,
    FFprobeMissingError,
)

__all__ = [
    "FFmpegBinaryMissingError",
    "FFmpegFrameExtractionProvider",
    "FFprobeEnricher",
    "FFprobeMissingError",
    "FrameExtractionArtifact",
]
