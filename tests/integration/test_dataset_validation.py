"""
Real dataset validation tests.

Runs the full pipeline against a short test video and validates
that the output is structurally correct end-to-end.
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
from sceneforge.knowledge.entity import EntityKind
from sceneforge.knowledge.scene_grouping_builder import SceneGroupingBuilder
from sceneforge.knowledge.storage import (
    InMemoryEntityStore,
    entity_build_key,
)
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
    tmpdir = tempfile.mkdtemp(prefix="sceneforge_ds_")
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


pytestmark = [
    pytest.mark.skipif(
        not _has_ffmpeg(), reason="ffmpeg/ffprobe not on PATH"
    ),
]


def test_short_video_produces_valid_output():
    """Full pipeline against a short test video: every stage succeeds
    and produces valid, non-empty output."""
    _scenedetect = pytest.importorskip("scenedetect")

    video_path, tmpdir = _try_load_video()
    try:
        # Load and enrich
        video = LocalVideoLoader(video_path).load()
        enriched = FFprobeEnricher().enrich(video)

        assert enriched.duration > 0
        assert enriched.metadata.get("probed") is True
        width = enriched.metadata.get("width", 0)
        height = enriched.metadata.get("height", 0)
        assert width > 0 and height > 0, (
            f"Expected dimensions, got {width}x{height}"
        )

        # Extract frames
        with tempfile.TemporaryDirectory() as frame_tmpdir:
            frame_artifacts = Pipeline(
                provider=FFmpegFrameExtractionProvider(
                    frame_count=4, output_dir=frame_tmpdir
                )
            ).run(enriched)
            assert len(frame_artifacts) == 4
            for art in frame_artifacts:
                assert Path(art.frame_path).is_file()
                assert art.frame_path.endswith(".png")

        # Detect scenes
        scene_artifacts = Pipeline(
            provider=PySceneDetectProvider()
        ).run(enriched)
        assert len(scene_artifacts) >= 1
        for art in scene_artifacts:
            assert art.start_seconds >= 0
            assert art.end_seconds > art.start_seconds or (
                art.start_seconds == 0 and art.end_seconds == 0
            )

        # Group into entities
        all_artifacts = list(frame_artifacts) + list(
            scene_artifacts
        )
        entities = SceneGroupingBuilder().build(all_artifacts)
        assert len(entities) >= 1

        for entity in entities:
            assert entity.kind == EntityKind.SCENE
            assert entity.builder == "scene_grouping"
            meta = entity.metadata
            assert "scene_index" in meta
            assert "start_seconds" in meta
            assert "end_seconds" in meta
            assert "media_id" in meta

        # Validate
        issues = validate_entities(entities)
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert errors == [], f"Validation errors: {errors}"

        # Store and round-trip
        store = InMemoryEntityStore()
        key = entity_build_key(
            all_artifacts, "scene_grouping", "1.0.0"
        )
        store.put(key, entities)
        retrieved = store.get(key)
        assert retrieved is not None
        assert len(retrieved) == len(entities)
    finally:
        if tmpdir is not None:
            shutil.rmtree(tmpdir, ignore_errors=True)
