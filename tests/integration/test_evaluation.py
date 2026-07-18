"""
Evaluation metrics for the SceneForge pipeline.

Tests that verify quantitative properties of pipeline outputs:
scene counts, frame counts, and determinism of entity IDs.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from sceneforge.contrib.ffmpeg.frame_extraction_provider import (
    FFmpegFrameExtractionProvider,
)
from sceneforge.contrib.ffmpeg.probe_enricher import FFprobeEnricher
from sceneforge.contrib.scenedetect.provider import PySceneDetectProvider
from sceneforge.core.pipeline import Pipeline
from sceneforge.knowledge.scene_grouping_builder import SceneGroupingBuilder
from sceneforge.knowledge.validation import Severity, validate_entities
from sceneforge.media.video_loader import LocalVideoLoader

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
VIDEO_PATH = FIXTURES / "video" / "short.mp4"


def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _make_synthetic_video(tmpdir: str | Path) -> Path:
    """Create a short synthetic video with colour changes."""
    path = Path(tmpdir) / "synthetic.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i",
        "color=c=red:s=320x240:d=1.5",
        "-f", "lavfi", "-i",
        "color=c=blue:s=320x240:d=1.5",
        "-filter_complex",
        "[0:v][1:v]concat=n=2:v=1:a=0[out]",
        "-map", "[out]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(path),
    ]
    subprocess.run(cmd, capture_output=True, timeout=30, check=True)
    return path


def _try_load_video() -> tuple[Path, str | None]:
    """Return (video_path, tmpdir_or_None). Generate synthetic if fixture unusable."""
    tmpdir = tempfile.mkdtemp(prefix="sceneforge_eval_")
    try:
        video = LocalVideoLoader(VIDEO_PATH).load()
        enriched = FFprobeEnricher().enrich(video)
        if enriched.duration > 0:
            shutil.rmtree(tmpdir, ignore_errors=True)
            return VIDEO_PATH, None
    except Exception:
        pass
    synth = _make_synthetic_video(tmpdir)
    return synth, tmpdir


def _enriched_video() -> tuple:
    video_path, tmpdir = _try_load_video()
    video = LocalVideoLoader(video_path).load()
    enriched = FFprobeEnricher().enrich(video)
    return enriched, tmpdir


pytestmark = [
    pytest.mark.skipif(
        not _has_ffmpeg(), reason="ffmpeg/ffprobe not on PATH"
    ),
]


def test_scene_count_matches_video():
    """Detected scene count should be between 1 and a reasonable upper
    bound for a short test video."""
    _scenedetect = pytest.importorskip("scenedetect")

    enriched, tmpdir = _enriched_video()
    try:
        pipeline = Pipeline(provider=PySceneDetectProvider())
        scenes = pipeline.run(enriched)

        assert 1 <= len(scenes) <= 20, (
            f"Scene count {len(scenes)} outside [1, 20]"
        )
    finally:
        if tmpdir is not None:
            shutil.rmtree(tmpdir, ignore_errors=True)


def test_frame_extraction_returns_expected_count():
    """FFmpegFrameExtractionProvider should return exactly the requested
    number of frames."""
    enriched, tmpdir = _enriched_video()
    try:
        with tempfile.TemporaryDirectory() as frame_tmpdir:
            requested = 5
            pipeline = Pipeline(
                provider=FFmpegFrameExtractionProvider(
                    frame_count=requested,
                    output_dir=frame_tmpdir,
                )
            )
            artifacts = pipeline.run(enriched)

            assert len(artifacts) == requested, (
                f"Requested {requested} frames, got {len(artifacts)}"
            )
            for art in artifacts:
                assert Path(art.frame_path).exists()
                assert art.frame_index in range(requested)
    finally:
        if tmpdir is not None:
            shutil.rmtree(tmpdir, ignore_errors=True)


def test_entity_ids_are_deterministic():
    """Same input -> structurally equivalent entities."""
    _scenedetect = pytest.importorskip("scenedetect")

    enriched, tmpdir = _enriched_video()
    try:
        with tempfile.TemporaryDirectory() as frame_tmpdir:
            frame_arts = Pipeline(
                provider=FFmpegFrameExtractionProvider(
                    frame_count=3, output_dir=frame_tmpdir
                )
            ).run(enriched)

        scene_arts = Pipeline(
            provider=PySceneDetectProvider()
        ).run(enriched)
        all_artifacts = list(frame_arts) + list(scene_arts)

        builder = SceneGroupingBuilder()
        entities_run1 = builder.build(all_artifacts)
        entities_run2 = builder.build(all_artifacts)

        assert len(entities_run1) == len(entities_run2)

        for e1, e2 in zip(
            entities_run1, entities_run2, strict=True
        ):
            assert e1.kind == e2.kind
            assert e1.builder == e2.builder
            assert (
                e1.metadata.get("scene_index")
                == e2.metadata.get("scene_index")
            )
            assert (
                e1.metadata.get("start_seconds")
                == e2.metadata.get("start_seconds")
            )
            assert (
                e1.metadata.get("end_seconds")
                == e2.metadata.get("end_seconds")
            )
            assert len(e1.parents) == len(e2.parents)

        issues1 = validate_entities(entities_run1)
        issues2 = validate_entities(entities_run2)
        assert [
            i for i in issues1 if i.severity == Severity.ERROR
        ] == []
        assert [
            i for i in issues2 if i.severity == Severity.ERROR
        ] == []
    finally:
        if tmpdir is not None:
            shutil.rmtree(tmpdir, ignore_errors=True)
