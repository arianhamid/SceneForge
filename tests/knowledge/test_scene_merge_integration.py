"""
Integration test for SceneMergeBuilder against REAL output from both
SceneGroupingBuilder and SceneFaceBuilder on the same real video --
the actual spike this builder exists to answer: can two independently-
built Knowledge Builders' output for the same scene be combined
without a new persistence or query concept?
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
from sceneforge.knowledge import (
    SceneFaceBuilder,
    SceneGroupingBuilder,
    SceneMergeBuilder,
)
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


def test_merges_real_dialogue_and_face_builders(
    video_with_two_scenes: Path, tmp_path: Path
):
    video_media = LocalVideoLoader(video_with_two_scenes).load()
    enricher = FFprobeEnricher()

    frame_provider = FFmpegFrameExtractionProvider(
        frame_count=4, output_dir=tmp_path / "frames"
    )
    frame_result = Pipeline(provider=frame_provider, enricher=enricher).run_detailed(
        video_media
    )
    scene_result = Pipeline(
        provider=PySceneDetectProvider(), enricher=enricher
    ).run_detailed(video_media)

    face_pipeline = Pipeline(
        provider=OpenCVFaceDetectionProvider(), enricher=OpenCVImageEnricher()
    )
    face_artifacts = []
    for frame_artifact in frame_result.artifacts:
        frame_media = LocalImageLoader(frame_artifact.frame_path).load()
        face_artifacts.extend(face_pipeline.run(frame_media))

    base_artifacts = [*frame_result.artifacts, *scene_result.artifacts]
    dialogue_entities = SceneGroupingBuilder().build(base_artifacts)
    face_entities = SceneFaceBuilder().build([*base_artifacts, *face_artifacts])

    merged = SceneMergeBuilder().relate([*dialogue_entities, *face_entities])

    assert len(merged) == 2  # one merged entity per real detected scene
    for entity in merged:
        assert set(entity.metadata["merged_from"]) == {"scene_grouping", "scene_face"}
        assert "frame_paths" in entity.metadata["scene_grouping"]
        assert "total_faces" in entity.metadata["scene_face"]
        # Both source builders agree on scene boundaries -- real evidence
        # the correlation key (media_id, scene_index) is actually shared.
        assert (
            entity.metadata["scene_grouping"]["start_seconds"]
            == entity.metadata["scene_face"]["start_seconds"]
        )
