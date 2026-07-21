"""
End-to-end integration tests for the full SceneForge pipeline.

Exercises: video loading -> enrichment -> frame extraction -> scene detection
-> scene grouping -> validation -> summary generation.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from sceneforge.applications.scene_summary import SceneSummary
from sceneforge.contrib.ffmpeg.frame_extraction_provider import (
    FFmpegFrameExtractionProvider,
)
from sceneforge.contrib.ffmpeg.probe_enricher import FFprobeEnricher
from sceneforge.contrib.scenedetect.provider import PySceneDetectProvider
from sceneforge.core.pipeline import Pipeline
from sceneforge.knowledge.scene_grouping_builder import SceneGroupingBuilder
from sceneforge.knowledge.storage import InMemoryEntityStore, entity_build_key
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
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=red:s=320x240:d=1.5",
        "-f",
        "lavfi",
        "-i",
        "color=c=blue:s=320x240:d=1.5",
        "-filter_complex",
        "[0:v][1:v]concat=n=2:v=1:a=0[out]",
        "-map",
        "[out]",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(path),
    ]
    subprocess.run(cmd, capture_output=True, timeout=30, check=True)
    return path


def _try_load_video() -> tuple[Path, Path | None]:
    """Return (video_path, tmpdir_or_None). Generate synthetic if fixture unusable."""
    tmpdir = tempfile.mkdtemp(prefix="sceneforge_test_")
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


# Skip if ffmpeg/ffprobe are not available at all
pytestmark = [
    pytest.mark.skipif(not _has_ffmpeg(), reason="ffmpeg/ffprobe not on PATH"),
]


def test_full_pipeline_video_to_summary():
    """Complete pipeline: load -> enrich -> extract frames -> detect scenes
    -> group -> validate -> summarize."""
    _scenedetect = pytest.importorskip("scenedetect")

    video_path, tmpdir = _try_load_video()
    try:
        # Step 1: Load video
        loader = LocalVideoLoader(video_path)
        video = loader.load()
        assert video.name

        # Step 2: Enrich with ffprobe
        enricher = FFprobeEnricher()
        enriched = enricher.enrich(video)
        assert enriched.duration > 0
        assert enriched.codec != "unknown"
        assert enriched.fps > 0

        # Step 3: Extract frames
        with tempfile.TemporaryDirectory() as frame_tmpdir:
            frame_pipeline = Pipeline(
                provider=FFmpegFrameExtractionProvider(
                    frame_count=3, output_dir=frame_tmpdir
                ),
                enricher=None,
            )
            frame_artifacts = frame_pipeline.run(enriched)
            assert len(frame_artifacts) == 3
            for art in frame_artifacts:
                assert Path(art.frame_path).exists()

        # Step 4: Detect scenes
        scene_pipeline = Pipeline(
            provider=PySceneDetectProvider(),
            enricher=None,
        )
        scene_artifacts = scene_pipeline.run(enriched)
        assert len(scene_artifacts) >= 1

        # Step 5: Group artifacts into scene entities
        all_artifacts = list(frame_artifacts) + list(scene_artifacts)
        builder = SceneGroupingBuilder()
        entities = builder.build(all_artifacts)
        assert len(entities) >= 1

        # Step 6: Validate entities
        issues = validate_entities(entities)
        errors = [i for i in issues if i.severity == Severity.ERROR]
        assert errors == [], f"Validation errors: {errors}"

        # Step 7: Store entities and generate summary
        store = InMemoryEntityStore()
        key = entity_build_key(all_artifacts, builder.name, builder.version)
        store.put(key, entities)

        summary = SceneSummary(store)
        data, markdown = summary.generate()
        assert len(data.scenes) >= 1
        assert "# Scene Summary" in markdown
        assert "scenes detected" in markdown
    finally:
        if tmpdir is not None:
            shutil.rmtree(tmpdir, ignore_errors=True)


def test_pipeline_returns_correct_artifact_types():
    """Verify each pipeline step produces the expected artifact kind."""
    _scenedetect = pytest.importorskip("scenedetect")

    video_path, tmpdir = _try_load_video()
    try:
        video = LocalVideoLoader(video_path).load()
        enriched = FFprobeEnricher().enrich(video)

        with tempfile.TemporaryDirectory() as frame_tmpdir:
            frame_pipeline = Pipeline(
                provider=FFmpegFrameExtractionProvider(
                    frame_count=2, output_dir=frame_tmpdir
                )
            )
            frame_arts = frame_pipeline.run(enriched)

        scene_pipeline = Pipeline(provider=PySceneDetectProvider())
        scene_arts = scene_pipeline.run(enriched)

        for art in frame_arts:
            assert hasattr(art, "frame_path")
            assert hasattr(art, "timestamp_seconds")

        for art in scene_arts:
            assert hasattr(art, "start_seconds")
            assert hasattr(art, "end_seconds")
            assert hasattr(art, "scene_index")
    finally:
        if tmpdir is not None:
            shutil.rmtree(tmpdir, ignore_errors=True)
