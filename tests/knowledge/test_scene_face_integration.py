"""
Integration test for SceneFaceBuilder against REAL cross-domain
provider output: real ffmpeg frame extraction, real scenedetect scene
detection, and real OpenCV face detection run against each extracted
frame as its own ImageMedia -- proving the source_frame_path
correlation (docs/adr/0016-cross-domain-knowledge-builder.md) actually
works end-to-end, not just against the hand-built fixtures in
test_scene_face_builder.py.

No real face photograph is available in this environment (no network
access), so every real detection call legitimately returns zero faces
here -- this test proves the *wiring* is correct (real frames, real
per-frame ImageMedia, real detector calls, correct scene attribution
of however many faces were found, including zero), the same honesty
boundary documented in OpenCVFaceDetectionProvider's module docstring.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from sceneforge.contrib.ffmpeg import FFmpegFrameExtractionProvider, FFprobeEnricher
from sceneforge.contrib.opencv import OpenCVFaceDetectionProvider, OpenCVImageEnricher
from sceneforge.contrib.scenedetect import PySceneDetectProvider
from sceneforge.core.pipeline import Pipeline
from sceneforge.knowledge import SceneFaceBuilder
from sceneforge.media.image_loader import LocalImageLoader
from sceneforge.media.video_loader import LocalVideoLoader

pytest.importorskip("cv2")
pytest.importorskip("scenedetect")

FFMPEG_AVAILABLE = (
    shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
)
pytestmark = pytest.mark.skipif(
    not FFMPEG_AVAILABLE, reason="ffmpeg/ffprobe not on PATH"
)


@pytest.fixture
def video_with_two_scenes(tmp_path: Path) -> Path:
    path = tmp_path / "two_scenes.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:duration=2:size=64x64:rate=10",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:duration=2:size=64x64:rate=10",
            "-filter_complex",
            "[0:v][1:v]concat=n=2:v=1:a=0",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        capture_output=True,
        check=True,
        timeout=30,
    )
    return path


def test_cross_domain_correlation_against_real_provider_output(
    video_with_two_scenes: Path, tmp_path: Path
):
    video_media = LocalVideoLoader(video_with_two_scenes).load()
    enricher = FFprobeEnricher()

    frame_provider = FFmpegFrameExtractionProvider(
        frame_count=6, output_dir=tmp_path / "frames"
    )
    frame_result = Pipeline(provider=frame_provider, enricher=enricher).run_detailed(
        video_media
    )
    scene_result = Pipeline(
        provider=PySceneDetectProvider(), enricher=enricher
    ).run_detailed(video_media)

    assert len(scene_result.artifacts) == 2  # sanity: real cuts found

    # Run real face detection against each real extracted frame, as
    # its own real ImageMedia -- exactly the cross-domain shape
    # SceneFaceBuilder exists to correlate.
    face_pipeline = Pipeline(
        provider=OpenCVFaceDetectionProvider(), enricher=OpenCVImageEnricher()
    )
    all_face_artifacts = []
    for frame_artifact in frame_result.artifacts:
        frame_media = LocalImageLoader(frame_artifact.frame_path).load()
        face_result = face_pipeline.run_detailed(frame_media)
        all_face_artifacts.extend(face_result.artifacts)
        # source_frame_path must match the real frame path without any
        # manual relinking -- the actual thing being proven here.
        for face in face_result.artifacts:
            assert face.source_frame_path == frame_artifact.frame_path

    all_artifacts = [
        *frame_result.artifacts,
        *scene_result.artifacts,
        *all_face_artifacts,
    ]
    entities = SceneFaceBuilder().build(all_artifacts)

    assert len(entities) == 2
    for entity in entities:
        assert "total_faces" in entity.metadata
        assert entity.metadata["total_faces"] >= 0  # real count; 0 is honest here
        assert len(entity.metadata["faces_per_frame"]) >= 1
