"""Tests for the EntityStore spike (docs/adr/0012-entity-persistence.md)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact
from sceneforge.knowledge.builder import build_with_cache
from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.exceptions import KnowledgeBuilderError
from sceneforge.knowledge.scene_grouping_builder import SceneGroupingBuilder
from sceneforge.knowledge.storage import (
    FileEntityStore,
    InMemoryEntityStore,
    entity_build_key,
    entity_from_dict,
    entity_to_dict,
    register_entity_type,
)


def _scene_cut(media_id, index, start, end):
    return SceneCutArtifact(
        media_id=media_id, scene_index=index, start_seconds=start, end_seconds=end
    )


def test_entity_round_trips_through_dict():
    entity = Entity(kind=EntityKind.SCENE, builder="scene_grouping", payload="hello")
    restored = entity_from_dict(entity_to_dict(entity))

    assert restored.id == entity.id
    assert restored.kind == entity.kind
    assert restored.builder == entity.builder
    assert restored.payload == entity.payload


def test_entity_metadata_and_parents_round_trip():
    parent_id = uuid4()
    entity = Entity(
        metadata={"scene_index": 0, "frame_paths": ["a.png"]}, parents=(parent_id,)
    )
    restored = entity_from_dict(entity_to_dict(entity))

    assert restored.metadata["scene_index"] == 0
    assert restored.metadata["frame_paths"] == ["a.png"]
    assert restored.parents == (parent_id,)


def test_file_entity_store_persists_across_instances(tmp_path):
    entity = Entity(kind=EntityKind.SCENE, payload="dialogue text")
    key = "some-key"

    FileEntityStore(tmp_path).put(key, [entity])

    reopened = FileEntityStore(tmp_path)
    cached = reopened.get(key)
    assert cached is not None
    assert cached[0].payload == "dialogue text"


def test_in_memory_entity_store_roundtrip():
    store = InMemoryEntityStore()
    store.put("k", [Entity(payload="x")])

    assert store.has("k")
    assert store.get("k")[0].payload == "x"

    store.delete("k")
    assert store.get("k") is None


def test_entity_build_key_stable_for_same_inputs():
    media_id = uuid4()
    artifacts = [_scene_cut(media_id, 0, 0.0, 2.0)]

    key1 = entity_build_key(artifacts, "scene_grouping", "1.0.0")
    key2 = entity_build_key(artifacts, "scene_grouping", "1.0.0")
    assert key1 == key2


def test_entity_build_key_independent_of_artifact_order():
    media_id = uuid4()
    a = _scene_cut(media_id, 0, 0.0, 2.0)
    b = _scene_cut(media_id, 1, 2.0, 4.0)

    key_ab = entity_build_key([a, b], "scene_grouping", "1.0.0")
    key_ba = entity_build_key([b, a], "scene_grouping", "1.0.0")
    assert key_ab == key_ba


def test_entity_build_key_changes_with_builder_version():
    media_id = uuid4()
    artifacts = [_scene_cut(media_id, 0, 0.0, 2.0)]

    key1 = entity_build_key(artifacts, "scene_grouping", "1.0.0")
    key2 = entity_build_key(artifacts, "scene_grouping", "2.0.0")
    assert key1 != key2


def test_entity_build_key_changes_when_artifact_set_changes():
    media_id = uuid4()
    a = _scene_cut(media_id, 0, 0.0, 2.0)
    b = _scene_cut(media_id, 1, 2.0, 4.0)

    key_a_only = entity_build_key([a], "scene_grouping", "1.0.0")
    key_a_and_b = entity_build_key([a, b], "scene_grouping", "1.0.0")
    assert key_a_only != key_a_and_b


def test_build_with_cache_without_store_just_calls_builder():
    media_id = uuid4()
    artifacts = [_scene_cut(media_id, 0, 0.0, 2.0)]

    entities = build_with_cache(SceneGroupingBuilder(), artifacts, store=None)
    assert len(entities) == 1


def test_build_with_cache_populates_and_reuses_cache():
    media_id = uuid4()
    artifacts = [_scene_cut(media_id, 0, 0.0, 2.0)]
    store = InMemoryEntityStore()

    call_count = 0
    builder = SceneGroupingBuilder()
    original_build = builder.build

    def counting_build(artifacts):
        nonlocal call_count
        call_count += 1
        return original_build(artifacts)

    builder.build = counting_build  # type: ignore[method-assign]

    first = build_with_cache(builder, artifacts, store=store)
    second = build_with_cache(builder, artifacts, store=store)

    assert call_count == 1  # second call was served from cache
    assert len(first) == len(second) == 1
    assert first[0].metadata["scene_index"] == second[0].metadata["scene_index"]


def test_build_with_cache_different_artifact_sets_are_different_cache_entries():
    media_id = uuid4()
    store = InMemoryEntityStore()
    builder = SceneGroupingBuilder()

    result_a = build_with_cache(
        builder, [_scene_cut(media_id, 0, 0.0, 2.0)], store=store
    )
    result_b = build_with_cache(
        builder, [_scene_cut(media_id, 0, 0.0, 3.0)], store=store
    )

    assert result_a[0].metadata["end_seconds"] == 2.0
    assert result_b[0].metadata["end_seconds"] == 3.0


def test_register_entity_type_enables_exact_roundtrip():
    from dataclasses import dataclass

    @register_entity_type
    @dataclass(frozen=True, slots=True)
    class CharacterEntity(Entity[str]):
        name: str = "unknown"

    entity = CharacterEntity(payload="a description", name="Alice")
    restored = entity_from_dict(entity_to_dict(entity))

    assert isinstance(restored, CharacterEntity)
    assert restored.name == "Alice"


def test_missing_scene_cuts_still_raises_through_cache_helper():
    media_id = uuid4()
    from sceneforge.contrib.ffmpeg.frame_extraction_artifact import (
        FrameExtractionArtifact,
    )

    artifacts = [FrameExtractionArtifact(media_id=media_id, timestamp_seconds=1.0)]

    with pytest.raises(KnowledgeBuilderError):
        build_with_cache(SceneGroupingBuilder(), artifacts, store=InMemoryEntityStore())
