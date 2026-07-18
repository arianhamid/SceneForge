"""
Tests for SceneSequenceBuilder's relationship logic, using hand-built
SCENE entities -- no real video needed to verify the sequencing math.
See tests/knowledge/test_relationship_integration.py for the version
fed by real provider + SceneGroupingBuilder output.
"""

from __future__ import annotations

from uuid import uuid4

from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.relationship_builder import SceneSequenceBuilder


def _scene(media_id, index):
    return Entity(
        kind=EntityKind.SCENE,
        builder="scene_grouping",
        metadata={"media_id": str(media_id), "scene_index": index},
    )


def test_links_consecutive_scenes():
    media_id = uuid4()
    scene0 = _scene(media_id, 0)
    scene1 = _scene(media_id, 1)
    scene2 = _scene(media_id, 2)

    relationships = SceneSequenceBuilder().relate([scene1, scene0, scene2])

    assert len(relationships) == 2
    assert all(r.kind == EntityKind.RELATIONSHIP for r in relationships)
    assert all(r.payload == "precedes" for r in relationships)


def test_relationship_parents_point_at_related_entities():
    media_id = uuid4()
    scene0 = _scene(media_id, 0)
    scene1 = _scene(media_id, 1)

    relationships = SceneSequenceBuilder().relate([scene0, scene1])

    assert len(relationships) == 1
    assert relationships[0].parents == (scene0.id, scene1.id)


def test_relationship_metadata_carries_scene_indices():
    media_id = uuid4()
    scene0 = _scene(media_id, 0)
    scene1 = _scene(media_id, 1)

    relationships = SceneSequenceBuilder().relate([scene0, scene1])
    rel = relationships[0]

    assert rel.metadata["source_scene_index"] == 0
    assert rel.metadata["target_scene_index"] == 1
    assert rel.metadata["relationship"] == "precedes"
    assert rel.metadata["source_entity_id"] == str(scene0.id)
    assert rel.metadata["target_entity_id"] == str(scene1.id)


def test_single_scene_produces_no_relationships():
    media_id = uuid4()
    relationships = SceneSequenceBuilder().relate([_scene(media_id, 0)])
    assert relationships == []


def test_no_scenes_produces_no_relationships():
    assert SceneSequenceBuilder().relate([]) == []


def test_different_media_ids_are_sequenced_separately():
    media_a, media_b = uuid4(), uuid4()
    a0, a1 = _scene(media_a, 0), _scene(media_a, 1)
    b0, b1 = _scene(media_b, 0), _scene(media_b, 1)

    relationships = SceneSequenceBuilder().relate([a0, a1, b0, b1])

    assert len(relationships) == 2
    media_ids_seen = {r.metadata["media_id"] for r in relationships}
    assert media_ids_seen == {str(media_a), str(media_b)}
    # No relationship should cross from media_a's scenes to media_b's.
    for r in relationships:
        assert r.metadata["media_id"] in (str(media_a), str(media_b))


def test_non_scene_entities_are_ignored():
    media_id = uuid4()
    scene0 = _scene(media_id, 0)
    scene1 = _scene(media_id, 1)
    unrelated = Entity(kind=EntityKind.CHARACTER, metadata={"media_id": str(media_id)})

    relationships = SceneSequenceBuilder().relate([scene0, unrelated, scene1])

    assert len(relationships) == 1


def test_entities_without_media_id_are_ignored():
    scene_without_media = Entity(kind=EntityKind.SCENE, metadata={"scene_index": 0})
    relationships = SceneSequenceBuilder().relate([scene_without_media])
    assert relationships == []


def test_builder_has_name_and_version():
    builder = SceneSequenceBuilder()
    assert builder.name == "scene_sequence"
    assert builder.version == "1.0.0"


def test_relationships_ordered_correctly_regardless_of_input_order():
    media_id = uuid4()
    scenes = [_scene(media_id, i) for i in (3, 1, 0, 2)]

    relationships = SceneSequenceBuilder().relate(scenes)

    pairs = [
        (r.metadata["source_scene_index"], r.metadata["target_scene_index"])
        for r in relationships
    ]
    assert pairs == [(0, 1), (1, 2), (2, 3)]
