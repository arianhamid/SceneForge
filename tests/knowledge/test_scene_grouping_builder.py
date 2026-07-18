"""
Tests for SceneGroupingBuilder's grouping logic, using hand-built
synthetic artifacts -- no real video, ffmpeg, or scenedetect needed to
verify the grouping math itself. See
tests/knowledge/test_scene_grouping_integration.py for the version
that feeds real provider output through this builder.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from sceneforge.contrib.ffmpeg.frame_extraction_artifact import FrameExtractionArtifact
from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact
from sceneforge.contrib.whisper.transcript_artifact import TranscriptSegmentArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.knowledge.entity import EntityKind
from sceneforge.knowledge.exceptions import KnowledgeBuilderError
from sceneforge.knowledge.scene_grouping_builder import SceneGroupingBuilder


def _scene_cut(media_id, index, start, end):
    return SceneCutArtifact(
        media_id=media_id, scene_index=index, start_seconds=start, end_seconds=end
    )


def _frame(media_id, timestamp, path="frame.png"):
    return FrameExtractionArtifact(
        media_id=media_id, timestamp_seconds=timestamp, frame_path=path
    )


def _segment(media_id, start, end, text):
    return TranscriptSegmentArtifact(
        media_id=media_id, start_seconds=start, end_seconds=end, payload=text
    )


def test_raises_without_scene_cuts():
    media_id = uuid4()
    builder = SceneGroupingBuilder()

    with pytest.raises(KnowledgeBuilderError):
        builder.build([_frame(media_id, 1.0)])


def test_groups_frames_by_scene():
    media_id = uuid4()
    artifacts = [
        _scene_cut(media_id, 0, 0.0, 2.0),
        _scene_cut(media_id, 1, 2.0, 4.0),
        _frame(media_id, 0.5, "a.png"),
        _frame(media_id, 1.5, "b.png"),
        _frame(media_id, 2.5, "c.png"),
    ]

    entities = SceneGroupingBuilder().build(artifacts)

    assert len(entities) == 2
    scene0, scene1 = sorted(entities, key=lambda e: e.metadata["scene_index"])
    assert scene0.metadata["frame_paths"] == ["a.png", "b.png"]
    assert scene1.metadata["frame_paths"] == ["c.png"]
    assert scene0.kind == EntityKind.SCENE


def test_frame_at_exact_scene_boundary_belongs_to_later_scene():
    """Half-open [start, end) -- a frame exactly at a cut belongs to the next scene."""
    media_id = uuid4()
    artifacts = [
        _scene_cut(media_id, 0, 0.0, 2.0),
        _scene_cut(media_id, 1, 2.0, 4.0),
        _frame(media_id, 2.0, "boundary.png"),
    ]

    entities = SceneGroupingBuilder().build(artifacts)
    scene0, scene1 = sorted(entities, key=lambda e: e.metadata["scene_index"])

    assert scene0.metadata["frame_paths"] == []
    assert scene1.metadata["frame_paths"] == ["boundary.png"]


def test_transcript_segment_assigned_to_overlapping_scene():
    media_id = uuid4()
    artifacts = [
        _scene_cut(media_id, 0, 0.0, 2.0),
        _scene_cut(media_id, 1, 2.0, 4.0),
        _segment(media_id, 0.5, 1.5, "hello there"),
        _segment(media_id, 2.5, 3.5, "general kenobi"),
    ]

    entities = SceneGroupingBuilder().build(artifacts)
    scene0, scene1 = sorted(entities, key=lambda e: e.metadata["scene_index"])

    assert scene0.payload == "hello there"
    assert scene1.payload == "general kenobi"


def test_transcript_segment_spanning_a_cut_belongs_to_both_scenes():
    media_id = uuid4()
    artifacts = [
        _scene_cut(media_id, 0, 0.0, 2.0),
        _scene_cut(media_id, 1, 2.0, 4.0),
        _segment(media_id, 1.5, 2.5, "spans the cut"),
    ]

    entities = SceneGroupingBuilder().build(artifacts)
    scene0, scene1 = sorted(entities, key=lambda e: e.metadata["scene_index"])

    assert scene0.payload == "spans the cut"
    assert scene1.payload == "spans the cut"
    assert scene0.metadata["transcript_segment_count"] == 1
    assert scene1.metadata["transcript_segment_count"] == 1


def test_transcript_segments_joined_in_time_order():
    media_id = uuid4()
    artifacts = [
        _scene_cut(media_id, 0, 0.0, 5.0),
        _segment(media_id, 3.0, 4.0, "second"),
        _segment(media_id, 0.0, 1.0, "first"),
    ]

    entities = SceneGroupingBuilder().build(artifacts)

    assert entities[0].payload == "first second"


def test_scene_with_no_dialogue_has_none_payload():
    media_id = uuid4()
    artifacts = [_scene_cut(media_id, 0, 0.0, 2.0)]

    entities = SceneGroupingBuilder().build(artifacts)

    assert entities[0].payload is None


def test_entity_parents_trace_back_to_contributing_artifacts():
    media_id = uuid4()
    cut = _scene_cut(media_id, 0, 0.0, 2.0)
    frame = _frame(media_id, 1.0)
    segment = _segment(media_id, 0.5, 1.5, "hi")

    entities = SceneGroupingBuilder().build([cut, frame, segment])

    parents = set(entities[0].parents)
    assert cut.id in parents
    assert frame.id in parents
    assert segment.id in parents


def test_different_media_ids_are_grouped_separately():
    media_a, media_b = uuid4(), uuid4()
    artifacts = [
        _scene_cut(media_a, 0, 0.0, 2.0),
        _scene_cut(media_b, 0, 0.0, 3.0),
        _frame(media_a, 1.0, "a.png"),
        _frame(media_b, 1.0, "b.png"),
    ]

    entities = SceneGroupingBuilder().build(artifacts)

    assert len(entities) == 2
    by_media = {e.metadata["media_id"]: e for e in entities}
    assert by_media[str(media_a)].metadata["frame_paths"] == ["a.png"]
    assert by_media[str(media_b)].metadata["frame_paths"] == ["b.png"]


def test_artifacts_without_media_id_are_ignored():
    media_id = uuid4()
    artifacts: list[Artifact] = [
        _scene_cut(media_id, 0, 0.0, 2.0),
        Artifact(provider="unrelated"),  # base Artifact has no media_id field
    ]

    entities = SceneGroupingBuilder().build(artifacts)

    assert len(entities) == 1


def test_builder_has_name_and_version():
    builder = SceneGroupingBuilder()
    assert builder.name == "scene_grouping"
    assert builder.version == "1.0.0"
