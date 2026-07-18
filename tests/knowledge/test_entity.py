"""Tests for the Entity base class."""

import pytest
from uuid import UUID, uuid4

from sceneforge.knowledge.entity import Entity, EntityKind, Provenance


def test_entity_has_default_kind():
    entity = Entity()
    assert entity.kind == EntityKind.ENTITY


def test_entity_is_immutable():
    entity = Entity(payload="hello")
    with pytest.raises(AttributeError):
        entity.payload = "changed"  # type: ignore[misc]


def test_entity_metadata_is_immutable():
    entity = Entity(metadata={"a": 1})
    with pytest.raises(TypeError):
        entity.metadata["a"] = 2  # type: ignore[index]


def test_entity_metadata_merges_from_dict():
    entity = Entity(metadata={"a": 1, "b": 2})
    assert entity.metadata["a"] == 1
    assert entity.metadata["b"] == 2


def test_entity_parents_default_empty():
    entity = Entity()
    assert entity.parents == ()


def test_entity_kind_values_are_strings():
    assert EntityKind.SCENE == "scene"
    assert EntityKind.CHARACTER == "character"


def test_entity_with_provenance():
    source_id = uuid4()
    provenance = Provenance(
        builder="test_builder",
        source_artifact_ids=(source_id,),
        confidence=0.95,
    )
    entity = Entity(provenance=provenance)
    assert entity.provenance is not None
    assert entity.provenance.builder == "test_builder"
    assert entity.provenance.source_artifact_ids == (source_id,)
    assert entity.provenance.confidence == 0.95


def test_entity_without_provenance():
    entity = Entity()
    assert entity.provenance is None
