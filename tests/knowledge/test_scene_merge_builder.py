"""
Tests for SceneMergeBuilder's merging logic, using hand-built entities
-- proves the (media_id, scene_index) correlation and namespacing
without needing real video or real providers. See
tests/knowledge/test_scene_merge_integration.py for the version fed by
real SceneGroupingBuilder + SceneFaceBuilder output.
"""

from __future__ import annotations

from uuid import uuid4

from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.scene_merge_builder import SceneMergeBuilder


def _scene_entity(media_id, scene_index, builder, **extra_metadata):
    metadata = {"media_id": str(media_id), "scene_index": scene_index, **extra_metadata}
    return Entity(
        kind=EntityKind.SCENE,
        builder=builder,
        payload=extra_metadata.pop("payload", None),
        metadata=metadata,
    )


def test_merges_two_builders_for_same_scene():
    media_id = uuid4()
    dialogue_entity = _scene_entity(
        media_id, 0, "scene_grouping", payload="hello", frame_paths=["a.png"]
    )
    face_entity = _scene_entity(media_id, 0, "scene_face", payload=2, total_faces=2)

    merged = SceneMergeBuilder().relate([dialogue_entity, face_entity])

    assert len(merged) == 1
    entity = merged[0]
    assert entity.kind == EntityKind.SCENE
    assert entity.builder == "scene_merge"
    merged_from = {"scene_grouping", "scene_face"}
    assert set(entity.metadata["merged_from"]) == merged_from


def test_merged_metadata_is_namespaced_by_builder():
    media_id = uuid4()
    dialogue_entity = _scene_entity(
        media_id, 0, "scene_grouping", payload="hello", frame_paths=["a.png"]
    )
    face_entity = _scene_entity(media_id, 0, "scene_face", payload=2, total_faces=2)

    merged = SceneMergeBuilder().relate([dialogue_entity, face_entity])[0]

    assert merged.metadata["scene_grouping"]["payload"] == "hello"
    assert merged.metadata["scene_grouping"]["frame_paths"] == ["a.png"]
    assert merged.metadata["scene_face"]["payload"] == 2
    assert merged.metadata["scene_face"]["total_faces"] == 2


def test_no_merge_when_only_one_builder_contributed():
    media_id = uuid4()
    only_entity = _scene_entity(media_id, 0, "scene_grouping", payload="hello")

    merged = SceneMergeBuilder().relate([only_entity])

    assert merged == []


def test_merge_parents_reference_both_source_entities():
    media_id = uuid4()
    dialogue_entity = _scene_entity(media_id, 0, "scene_grouping", payload="hello")
    face_entity = _scene_entity(media_id, 0, "scene_face", payload=2)

    merged = SceneMergeBuilder().relate([dialogue_entity, face_entity])[0]

    assert set(merged.parents) == {dialogue_entity.id, face_entity.id}


def test_different_scenes_are_not_merged_together():
    media_id = uuid4()
    scene0_a = _scene_entity(media_id, 0, "scene_grouping", payload="a")
    scene0_b = _scene_entity(media_id, 0, "scene_face", payload=1)
    scene1_a = _scene_entity(media_id, 1, "scene_grouping", payload="b")
    scene1_b = _scene_entity(media_id, 1, "scene_face", payload=2)

    merged = SceneMergeBuilder().relate([scene0_a, scene0_b, scene1_a, scene1_b])

    assert len(merged) == 2
    scene_indices = {e.metadata["scene_index"] for e in merged}
    assert scene_indices == {0, 1}


def test_different_media_ids_are_not_merged_together():
    media_a, media_b = uuid4(), uuid4()
    a1 = _scene_entity(media_a, 0, "scene_grouping", payload="a")
    a2 = _scene_entity(media_a, 0, "scene_face", payload=1)
    b1 = _scene_entity(media_b, 0, "scene_grouping", payload="b")
    b2 = _scene_entity(media_b, 0, "scene_face", payload=2)

    merged = SceneMergeBuilder().relate([a1, a2, b1, b2])

    assert len(merged) == 2
    media_ids = {e.metadata["media_id"] for e in merged}
    assert media_ids == {str(media_a), str(media_b)}


def test_three_builders_merge_into_one_entity():
    media_id = uuid4()
    entities = [
        _scene_entity(media_id, 0, "scene_grouping", payload="hi"),
        _scene_entity(media_id, 0, "scene_face", payload=1),
        _scene_entity(media_id, 0, "some_future_builder", payload="extra"),
    ]

    merged = SceneMergeBuilder().relate(entities)
    expected = {"scene_grouping", "scene_face", "some_future_builder"}

    assert len(merged) == 1
    assert set(merged[0].metadata["merged_from"]) == expected


def test_non_scene_entities_are_ignored():
    media_id = uuid4()
    scene_a = _scene_entity(media_id, 0, "scene_grouping", payload="hi")
    scene_b = _scene_entity(media_id, 0, "scene_face", payload=1)
    unrelated = Entity(
        kind=EntityKind.RELATIONSHIP, metadata={"media_id": str(media_id)}
    )

    merged = SceneMergeBuilder().relate([scene_a, scene_b, unrelated])

    assert len(merged) == 1


def test_builder_has_name_and_version():
    builder = SceneMergeBuilder()
    assert builder.name == "scene_merge"
    assert builder.version == "1.0.0"


def test_empty_input_produces_empty_output():
    assert SceneMergeBuilder().relate([]) == []
