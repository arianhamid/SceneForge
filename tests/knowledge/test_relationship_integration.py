"""
Integration test for SceneSequenceBuilder against REAL SceneGroupingBuilder
output, which is itself built from REAL ffmpeg + scenedetect output.

This is the two-stage Knowledge layer proven end-to-end:
  real Providers -> SceneGroupingBuilder (Artifact -> Entity)
                  -> SceneSequenceBuilder (Entity -> Entity)

confirming the RelationshipBuilder Protocol split (ADR-0013) actually
works with genuinely produced data, not just hand-built fixtures.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from sceneforge.contrib.ffmpeg import FFmpegFrameExtractionProvider, FFprobeEnricher
from sceneforge.contrib.scenedetect import PySceneDetectProvider
from sceneforge.core.pipeline import Pipeline
from sceneforge.knowledge import EntityKind, SceneGroupingBuilder, SceneSequenceBuilder

pytest.importorskip("scenedetect")

FFMPEG_AVAILABLE = (
    shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
)
pytestmark = pytest.mark.skipif(
    not FFMPEG_AVAILABLE, reason="ffmpeg/ffprobe not on PATH"
)


@pytest.fixture
def video_with_three_scenes(tmp_path: Path) -> Path:
    """A real video with three distinct, unambiguous scenes: red, green, blue."""
    path = tmp_path / "three_scenes.mp4"
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
            "color=c=green:duration=2:size=64x64:rate=10",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:duration=2:size=64x64:rate=10",
            "-filter_complex",
            "[0:v][1:v][2:v]concat=n=3:v=1:a=0",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        capture_output=True,
        check=True,
        timeout=30,
    )
    return path


def test_scene_sequence_from_real_three_scene_video(video_with_three_scenes: Path):
    from sceneforge.media.video_loader import LocalVideoLoader

    media = LocalVideoLoader(video_with_three_scenes).load()
    enricher = FFprobeEnricher()

    frame_result = Pipeline(
        provider=FFmpegFrameExtractionProvider(frame_count=6), enricher=enricher
    ).run_detailed(media)
    scene_result = Pipeline(
        provider=PySceneDetectProvider(), enricher=enricher
    ).run_detailed(media)

    assert len(scene_result.artifacts) == 3  # sanity: real cuts actually found

    all_artifacts = [*frame_result.artifacts, *scene_result.artifacts]
    scenes = SceneGroupingBuilder().build(all_artifacts)
    relationships = SceneSequenceBuilder().relate(scenes)

    assert len(scenes) == 3
    assert len(relationships) == 2  # scene0->1, scene1->2
    assert all(r.kind == EntityKind.RELATIONSHIP for r in relationships)

    pairs = sorted(
        (r.metadata["source_scene_index"], r.metadata["target_scene_index"])
        for r in relationships
    )
    assert pairs == [(0, 1), (1, 2)]

    # Every relationship's parents should resolve to real scene entity ids.
    scene_ids = {s.id for s in scenes}
    for r in relationships:
        assert set(r.parents).issubset(scene_ids)


def test_relationship_entity_round_trips_through_entity_store():
    from sceneforge.knowledge.storage import entity_from_dict, entity_to_dict

    media_id_a = "media-a"
    from sceneforge.knowledge.entity import Entity

    scene0 = Entity(
        kind=EntityKind.SCENE, metadata={"media_id": media_id_a, "scene_index": 0}
    )
    scene1 = Entity(
        kind=EntityKind.SCENE, metadata={"media_id": media_id_a, "scene_index": 1}
    )

    relationship = SceneSequenceBuilder().relate([scene0, scene1])[0]
    restored = entity_from_dict(entity_to_dict(relationship))

    assert restored.kind == EntityKind.RELATIONSHIP
    assert restored.parents == relationship.parents
    assert restored.metadata["relationship"] == "precedes"
