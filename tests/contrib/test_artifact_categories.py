"""
Confirms every real artifact type sets a meaningful ArtifactCategory,
not just the frozen dataclass default.

ArtifactCategory existed with zero real consumers before this: every
shipped artifact type silently defaulted to METADATA regardless of
what it actually represented (a detection, an analysis result, a
derived file). This test locks in the real values now that they're
set, so a future artifact type that forgets to set one is at least
visible here rather than silently joining the same gap.
"""

from __future__ import annotations

from sceneforge.contrib.ffmpeg.frame_extraction_artifact import FrameExtractionArtifact
from sceneforge.contrib.media_hash.artifact import MediaHashArtifact
from sceneforge.contrib.opencv.face_detection_artifact import FaceDetectionArtifact
from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact
from sceneforge.contrib.whisper.transcript_artifact import TranscriptSegmentArtifact
from sceneforge.core.artifact import ArtifactCategory


def test_frame_extraction_is_derived():
    assert FrameExtractionArtifact().category == ArtifactCategory.DERIVED


def test_scene_cut_is_analysis():
    assert SceneCutArtifact().category == ArtifactCategory.ANALYSIS


def test_transcript_segment_is_analysis():
    assert TranscriptSegmentArtifact().category == ArtifactCategory.ANALYSIS


def test_face_detection_is_detection():
    assert FaceDetectionArtifact().category == ArtifactCategory.DETECTION


def test_media_hash_is_metadata():
    # METADATA is the correct category here, not a leftover default --
    # a content hash genuinely is identity metadata about the file.
    assert MediaHashArtifact().category == ArtifactCategory.METADATA
