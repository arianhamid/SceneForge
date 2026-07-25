"""
Integration test for FactExtractionBuilder against REAL provider output.

Real ffmpeg-generated image + real LocalImageLoader + real Pipeline
(validation, enrichment, caching) + real TransformersCaptionProvider,
all run through their actual machinery, feeding the real
CaptionArtifact this produces into FactExtractionBuilder -- the same
discipline as tests/knowledge/test_scene_grouping_integration.py.

The captioning model itself is a fake (see
tests/contrib/test_transformers_caption.py for why -- no network
access to the Hugging Face Hub, no torch installed here). Everything
else in this test is completely real.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from sceneforge.contrib.transformers_caption import (
    CaptionArtifact,
    TransformersCaptionProvider,
)
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.storage import InMemoryArtifactStore
from sceneforge.knowledge.entity import EntityKind
from sceneforge.knowledge.fact_extraction_builder import FactExtractionBuilder
from sceneforge.media.image_loader import LocalImageLoader

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None
pytestmark = pytest.mark.skipif(not FFMPEG_AVAILABLE, reason="ffmpeg not on PATH")


class FakeCaptionPipeline:
    """Deterministic fake standing in for a real transformers pipeline
    (see ADR-0010's dependency-injection pattern)."""

    def __call__(self, images, text=None, **kwargs):
        # Pretend the real (solid green) frame was captioned correctly.
        return [{"generated_text": "a solid green frame"}]


@pytest.fixture
def real_green_frame(tmp_path: Path) -> Path:
    """A real PNG file: one solid green frame, rendered by real ffmpeg."""
    path = tmp_path / "frame.png"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=green:size=64x64",
            "-frames:v",
            "1",
            str(path),
        ],
        check=True,
        capture_output=True,
    )
    return path


def test_real_frame_through_pipeline_and_fact_extraction(real_green_frame: Path):
    media = LocalImageLoader(real_green_frame).load()
    store = InMemoryArtifactStore()
    provider = TransformersCaptionProvider(FakeCaptionPipeline())
    pipeline = Pipeline(provider=provider, store=store)

    result = pipeline.run_detailed(media)

    assert len(result.artifacts) == 1
    caption_artifact = result.artifacts[0]
    assert isinstance(caption_artifact, CaptionArtifact)
    assert caption_artifact.payload == "a solid green frame"
    assert caption_artifact.media_id == media.id

    builder = FactExtractionBuilder()
    entities = builder.build(result.artifacts)

    assert len(entities) == 1
    fact = entities[0]
    assert fact.kind == EntityKind.FACT
    assert fact.payload == "a solid green frame"
    assert fact.parents == (caption_artifact.id,)
    assert fact.provenance is not None
    assert fact.provenance.source_artifact_ids == (caption_artifact.id,)
    assert fact.metadata["media_id"] == str(media.id)


def test_real_frame_caption_is_cached_on_second_pipeline_run(
    real_green_frame: Path,
):
    """Proves the whole real chain -- not just the builder -- including the
    ADR-0024 content-identity cache: reloading the same unchanged file is a
    cache hit, not a re-run."""
    store = InMemoryArtifactStore()
    provider = TransformersCaptionProvider(FakeCaptionPipeline())

    first_media = LocalImageLoader(real_green_frame).load()
    first_result = Pipeline(provider=provider, store=store).run_detailed(first_media)
    assert first_result.from_cache is False

    second_media = LocalImageLoader(real_green_frame).load()
    second_result = Pipeline(provider=provider, store=store).run_detailed(second_media)
    assert second_result.from_cache is True

    builder = FactExtractionBuilder()
    entities = builder.build(second_result.artifacts)
    assert len(entities) == 1
    assert entities[0].payload == "a solid green frame"
