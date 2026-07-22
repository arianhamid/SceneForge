"""Tests for the EntityStore spike (docs/adr/0012-entity-persistence.md)."""

from __future__ import annotations

import json
from uuid import uuid4

import pytest

from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact
from sceneforge.core.exceptions import ArtifactSerializationError
from sceneforge.knowledge.builder import build_with_cache
from sceneforge.knowledge.entity import Entity, EntityKind, Provenance
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


def test_entity_provenance_round_trips_through_dict():
    """Regression test for the 2026-07-22 implementation review's Critical 2:
    JSON persistence through `FileEntityStore` previously raised
    `TypeError: Object of type Provenance is not JSON serializable` for any
    Entity carrying real Provenance, so no production builder could safely
    populate the field.

    Goes through real `json.dumps`/`json.loads`, not just the codec
    functions in memory: without the fix, `_serialize_value` silently
    passed the `Provenance` object through unchanged, so a dict-only round
    trip would pass even on the broken code and prove nothing."""
    source_id = uuid4()
    provenance = Provenance(
        builder="scene_face_builder", source_artifact_ids=(source_id,), confidence=0.82
    )
    entity = Entity(kind=EntityKind.SCENE, provenance=provenance)

    serialized = entity_to_dict(entity)
    json_round_tripped = json.loads(json.dumps(serialized))
    restored = entity_from_dict(json_round_tripped)

    assert restored.provenance == provenance
    assert restored.provenance.source_artifact_ids == (source_id,)


def test_entity_without_provenance_round_trips_as_none():
    entity = Entity(kind=EntityKind.SCENE, provenance=None)

    restored = entity_from_dict(entity_to_dict(entity))

    assert restored.provenance is None


def test_entity_from_legacy_dict_without_provenance_defaults_to_none():
    data = entity_to_dict(Entity(kind=EntityKind.SCENE))
    data.pop("provenance")

    restored = entity_from_dict(json.loads(json.dumps(data)))

    assert restored.provenance is None


def test_entity_from_dict_wraps_missing_provenance_builder_key():
    data = entity_to_dict(Entity(kind=EntityKind.SCENE))
    data["provenance"] = {"source_artifact_ids": [], "confidence": 0.5}  # no "builder"

    with pytest.raises(ArtifactSerializationError) as exc_info:
        entity_from_dict(data)

    assert isinstance(exc_info.value.__cause__, KeyError)


def test_entity_from_dict_wraps_malformed_provenance_uuid():
    data = entity_to_dict(Entity(kind=EntityKind.SCENE))
    data["provenance"] = {
        "builder": "x",
        "source_artifact_ids": ["not-a-uuid"],
        "confidence": None,
    }

    with pytest.raises(ArtifactSerializationError) as exc_info:
        entity_from_dict(data)

    assert isinstance(exc_info.value.__cause__, ValueError)


@pytest.mark.parametrize(
    "provenance",
    [
        "not-a-mapping",
        17,
        {"builder": 17},
        {"builder": "x", "source_artifact_ids": [17]},
        {"builder": "x", "confidence": "high"},
    ],
)
def test_entity_from_dict_rejects_invalid_provenance_types(provenance: object):
    data = entity_to_dict(Entity(kind=EntityKind.SCENE))
    data["provenance"] = provenance

    with pytest.raises(ArtifactSerializationError) as exc_info:
        entity_from_dict(data)

    assert isinstance(exc_info.value.__cause__, TypeError)


def test_entity_from_dict_wraps_malformed_type_tag():
    data = entity_to_dict(Entity(kind=EntityKind.SCENE))
    data["__type__"] = []

    with pytest.raises(ArtifactSerializationError) as exc_info:
        entity_from_dict(data)

    assert isinstance(exc_info.value.__cause__, TypeError)


def test_registered_entity_subclass_round_trips_with_provenance():
    from dataclasses import dataclass

    @register_entity_type
    @dataclass(frozen=True, slots=True)
    class ProvenancedCharacterEntity(Entity[str]):
        name: str = "unknown"

    provenance = Provenance(builder="scene_face_builder", confidence=0.9)
    entity = ProvenancedCharacterEntity(
        payload="a description", name="Alice", provenance=provenance
    )
    serialized = json.loads(json.dumps(entity_to_dict(entity)))
    restored = entity_from_dict(serialized)

    assert isinstance(restored, ProvenancedCharacterEntity)
    assert restored.provenance == provenance


def test_file_entity_store_persists_entity_with_provenance(tmp_path):
    """The same regression as above, but exercised through the real, JSON-backed
    store rather than the dict codec in isolation -- this is the path a real
    Knowledge Builder actually uses."""
    source_id = uuid4()
    provenance = Provenance(
        builder="scene_text_builder", source_artifact_ids=(source_id,), confidence=0.5
    )
    entity = Entity(kind=EntityKind.SCENE, provenance=provenance)
    key = "provenance-key"

    FileEntityStore(tmp_path).put(key, [entity])

    reopened = FileEntityStore(tmp_path)
    cached = reopened.get(key)
    assert cached is not None
    assert cached[0].provenance == provenance


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
