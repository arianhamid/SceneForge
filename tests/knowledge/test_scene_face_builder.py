"""
Tests for SceneFaceBuilder's cross-domain correlation logic, using
hand-built artifacts -- proves the frame-path matching math without
needing real video or a real face photograph. See
tests/knowledge/test_scene_face_integration.py for the version fed by
real ffmpeg + scenedetect + opencv output.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from sceneforge.contrib.ffmpeg.frame_extraction_artifact import FrameExtractionArtifact
from sceneforge.contrib.opencv.face_detection_artifact import FaceDetectionArtifact
from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact
from sceneforge.knowledge.exceptions import KnowledgeBuilderError
from sceneforge.knowledge.scene_face_builder import SceneFaceBuilder


def _scene_cut(media_id, index, start, end):
    return SceneCutArtifact(
        media_id=media_id, scene_index=index, start_seconds=start, end_seconds=end
    )


def _frame(media_id, timestamp, path):
    return FrameExtractionArtifact(
        media_id=media_id, timestamp_seconds=timestamp, frame_path=path
    )


def _face(source_frame_path, index=0):
    # media_id is deliberately a random, unrelated id -- the whole
    # point of source_frame_path-based correlation is that this
    # doesn't need to match the video's media_id.
    return FaceDetectionArtifact(
        media_id=uuid4(),
        provider="opencv_face_detection",
        source_frame_path=source_frame_path,
    )


def test_raises_without_scene_cuts():
    media_id = uuid4()
    with pytest.raises(KnowledgeBuilderError):
        SceneFaceBuilder().build([_frame(media_id, 1.0, "f.png")])


def test_face_media_id_does_not_need_to_match_video_media_id():
    """The core spike finding: correlation is by source_frame_path, not media_id."""
    media_id = uuid4()
    frame = _frame(media_id, 0.5, "frame_0.png")
    face = _face("frame_0.png")
    assert face.media_id != media_id  # sanity: genuinely unrelated ids

    artifacts = [_scene_cut(media_id, 0, 0.0, 2.0), frame, face]
    entities = SceneFaceBuilder().build(artifacts)

    assert len(entities) == 1
    assert entities[0].metadata["total_faces"] == 1


def test_faces_counted_per_frame_and_totaled_per_scene():
    media_id = uuid4()
    frame_a = _frame(media_id, 0.5, "a.png")
    frame_b = _frame(media_id, 1.5, "b.png")
    artifacts = [
        _scene_cut(media_id, 0, 0.0, 2.0),
        frame_a,
        frame_b,
        _face("a.png"),
        _face("a.png"),
        _face("b.png"),
    ]

    entities = SceneFaceBuilder().build(artifacts)

    assert len(entities) == 1
    metadata = entities[0].metadata
    assert metadata["total_faces"] == 3
    assert metadata["faces_per_frame"] == {"a.png": 2, "b.png": 1}
    assert entities[0].payload == 3


def test_frame_with_no_faces_is_still_reported_with_zero():
    media_id = uuid4()
    frame = _frame(media_id, 0.5, "empty.png")
    artifacts = [_scene_cut(media_id, 0, 0.0, 2.0), frame]

    entities = SceneFaceBuilder().build(artifacts)

    assert entities[0].metadata["faces_per_frame"] == {"empty.png": 0}
    assert entities[0].metadata["total_faces"] == 0


def test_faces_correctly_split_across_scenes():
    media_id = uuid4()
    artifacts = [
        _scene_cut(media_id, 0, 0.0, 2.0),
        _scene_cut(media_id, 1, 2.0, 4.0),
        _frame(media_id, 0.5, "scene0.png"),
        _frame(media_id, 2.5, "scene1.png"),
        _face("scene0.png"),
        _face("scene1.png"),
        _face("scene1.png"),
    ]

    entities = SceneFaceBuilder().build(artifacts)
    scene0, scene1 = sorted(entities, key=lambda e: e.metadata["scene_index"])

    assert scene0.metadata["total_faces"] == 1
    assert scene1.metadata["total_faces"] == 2


def test_face_with_unmatched_frame_path_is_silently_uncounted():
    """
    A face detection whose source_frame_path doesn't match any known
    frame (e.g. from a differently-sourced image) shouldn't crash or
    get attributed anywhere -- it's simply not part of this media's
    scene structure.
    """
    media_id = uuid4()
    artifacts = [
        _scene_cut(media_id, 0, 0.0, 2.0),
        _frame(media_id, 0.5, "known.png"),
        _face("totally_unrelated.png"),
    ]

    entities = SceneFaceBuilder().build(artifacts)

    assert entities[0].metadata["total_faces"] == 0


def test_entity_parents_include_faces_frames_and_scene_cut():
    media_id = uuid4()
    cut = _scene_cut(media_id, 0, 0.0, 2.0)
    frame = _frame(media_id, 0.5, "f.png")
    face = _face("f.png")

    entities = SceneFaceBuilder().build([cut, frame, face])

    parents = set(entities[0].parents)
    assert cut.id in parents
    assert frame.id in parents
    assert face.id in parents


def test_different_media_ids_are_grouped_separately():
    media_a, media_b = uuid4(), uuid4()
    artifacts = [
        _scene_cut(media_a, 0, 0.0, 2.0),
        _scene_cut(media_b, 0, 0.0, 2.0),
        _frame(media_a, 0.5, "a.png"),
        _frame(media_b, 0.5, "b.png"),
        _face("a.png"),
    ]

    entities = SceneFaceBuilder().build(artifacts)

    by_media = {e.metadata["media_id"]: e for e in entities}
    assert by_media[str(media_a)].metadata["total_faces"] == 1
    assert by_media[str(media_b)].metadata["total_faces"] == 0


def test_builder_has_name_and_version():
    builder = SceneFaceBuilder()
    assert builder.name == "scene_face"
    assert builder.version == "1.0.0"
