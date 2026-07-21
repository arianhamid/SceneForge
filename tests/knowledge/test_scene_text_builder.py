"""
Tests for SceneTextBuilder's cross-domain correlation logic, using
hand-built artifacts -- proves the frame-path matching math without
needing real video or real rendered text. See
tests/knowledge/test_scene_text_integration.py for the version fed by
real ffmpeg + scenedetect + tesseract output.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from sceneforge.contrib.ffmpeg.frame_extraction_artifact import FrameExtractionArtifact
from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact
from sceneforge.contrib.tesseract.ocr_artifact import OCRTextArtifact
from sceneforge.knowledge.exceptions import KnowledgeBuilderError
from sceneforge.knowledge.scene_text_builder import SceneTextBuilder


def _scene_cut(media_id, index, start, end):
    return SceneCutArtifact(
        media_id=media_id, scene_index=index, start_seconds=start, end_seconds=end
    )


def _frame(media_id, timestamp, path):
    return FrameExtractionArtifact(
        media_id=media_id, timestamp_seconds=timestamp, frame_path=path
    )


def _word(source_frame_path, text, word_index=0):
    return OCRTextArtifact(
        media_id=uuid4(),
        provider="tesseract_ocr",
        payload=text,
        word_index=word_index,
        source_frame_path=source_frame_path,
    )


def test_raises_without_scene_cuts():
    media_id = uuid4()
    with pytest.raises(KnowledgeBuilderError):
        SceneTextBuilder().build([_frame(media_id, 1.0, "f.png")])


def test_word_media_id_does_not_need_to_match_video_media_id():
    media_id = uuid4()
    frame = _frame(media_id, 0.5, "frame_0.png")
    word = _word("frame_0.png", "HELLO")
    assert word.media_id != media_id

    artifacts = [_scene_cut(media_id, 0, 0.0, 2.0), frame, word]
    entities = SceneTextBuilder().build(artifacts)

    assert len(entities) == 1
    assert entities[0].payload == "HELLO"


def test_words_joined_in_reading_order_within_a_frame():
    media_id = uuid4()
    frame = _frame(media_id, 0.5, "f.png")
    artifacts = [
        _scene_cut(media_id, 0, 0.0, 2.0),
        frame,
        _word("f.png", "WORLD", word_index=1),
        _word("f.png", "HELLO", word_index=0),
    ]

    entities = SceneTextBuilder().build(artifacts)

    assert entities[0].payload == "HELLO WORLD"


def test_text_correctly_split_across_scenes():
    media_id = uuid4()
    artifacts = [
        _scene_cut(media_id, 0, 0.0, 2.0),
        _scene_cut(media_id, 1, 2.0, 4.0),
        _frame(media_id, 0.5, "scene0.png"),
        _frame(media_id, 2.5, "scene1.png"),
        _word("scene0.png", "EXIT"),
        _word("scene1.png", "POLICE"),
    ]

    entities = SceneTextBuilder().build(artifacts)
    scene0, scene1 = sorted(entities, key=lambda e: e.metadata["scene_index"])

    assert scene0.payload == "EXIT"
    assert scene1.payload == "POLICE"


def test_frame_with_no_text_reports_empty_string():
    media_id = uuid4()
    frame = _frame(media_id, 0.5, "empty.png")
    artifacts = [_scene_cut(media_id, 0, 0.0, 2.0), frame]

    entities = SceneTextBuilder().build(artifacts)

    assert entities[0].metadata["text_per_frame"] == {"empty.png": ""}
    assert entities[0].payload is None


def test_multiple_frames_joined_with_slash_separator():
    media_id = uuid4()
    frame_a = _frame(media_id, 0.5, "a.png")
    frame_b = _frame(media_id, 1.5, "b.png")
    artifacts = [
        _scene_cut(media_id, 0, 0.0, 2.0),
        frame_a,
        frame_b,
        _word("a.png", "EXIT"),
        _word("b.png", "POLICE"),
    ]

    entities = SceneTextBuilder().build(artifacts)

    assert entities[0].payload == "EXIT / POLICE"


def test_entity_parents_include_words_frames_and_scene_cut():
    media_id = uuid4()
    cut = _scene_cut(media_id, 0, 0.0, 2.0)
    frame = _frame(media_id, 0.5, "f.png")
    word = _word("f.png", "HELLO")

    entities = SceneTextBuilder().build([cut, frame, word])

    parents = set(entities[0].parents)
    assert cut.id in parents
    assert frame.id in parents
    assert word.id in parents


def test_builder_has_name_and_version():
    builder = SceneTextBuilder()
    assert builder.name == "scene_text"
    assert builder.version == "1.0.0"
