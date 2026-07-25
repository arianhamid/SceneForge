"""Tests for the durable evidence/knowledge record store
(ADR-0024 Phase 0 item 4), distinct from EntityStore's cache role."""

from __future__ import annotations

import tempfile

import pytest

from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.storage import (
    FileKnowledgeRecordStore,
    InMemoryKnowledgeRecordStore,
    KnowledgeRecord,
)


def _entity(payload: str = "hello") -> Entity[str]:
    return Entity(kind=EntityKind.SCENE, payload=payload)


def test_append_creates_revision_one_for_a_new_key():
    store = InMemoryKnowledgeRecordStore()

    record = store.append("k1", [_entity()])

    assert record.revision == 1
    assert record.key == "k1"
    assert not record.retracted


def test_append_twice_creates_a_second_revision_not_an_overwrite():
    store = InMemoryKnowledgeRecordStore()
    store.append("k1", [_entity("first")])
    second = store.append("k1", [_entity("second")])

    assert second.revision == 2
    history = store.history("k1")
    assert [r.revision for r in history] == [1, 2]
    assert history[0].entities[0].payload == "first"
    assert history[1].entities[0].payload == "second"


def test_latest_returns_the_most_recent_revision():
    store = InMemoryKnowledgeRecordStore()
    store.append("k1", [_entity("first")])
    store.append("k1", [_entity("second")])

    latest = store.latest("k1")

    assert latest is not None
    assert latest.revision == 2
    assert latest.entities[0].payload == "second"


def test_latest_returns_none_for_an_unknown_key():
    store = InMemoryKnowledgeRecordStore()
    assert store.latest("nope") is None


def test_history_returns_empty_list_for_an_unknown_key():
    store = InMemoryKnowledgeRecordStore()
    assert store.history("nope") == []


def test_retract_appends_a_new_revision_rather_than_deleting():
    store = InMemoryKnowledgeRecordStore()
    store.append("k1", [_entity("first")])

    retraction = store.retract("k1", reason="corrected by re-run")

    assert retraction.revision == 2
    assert retraction.retracted
    assert retraction.retracted_reason == "corrected by re-run"
    assert retraction.entities == ()
    # The original revision is still there, unmodified.
    history = store.history("k1")
    assert len(history) == 2
    assert not history[0].retracted
    assert history[0].entities[0].payload == "first"


def test_latest_after_retraction_is_the_retraction_itself():
    """A retraction is itself the latest fact about `key` until superseded
    again -- callers wanting the last non-retracted answer must inspect
    history() themselves, per KnowledgeRecordStore's documented contract."""
    store = InMemoryKnowledgeRecordStore()
    store.append("k1", [_entity()])
    store.retract("k1", reason="wrong")

    latest = store.latest("k1")

    assert latest is not None
    assert latest.retracted


def test_keys_lists_every_key_with_at_least_one_revision():
    store = InMemoryKnowledgeRecordStore()
    store.append("k1", [_entity()])
    store.append("k2", [_entity()])

    assert sorted(store.keys()) == ["k1", "k2"]


def test_file_store_persists_revisions_across_instances(tmp_path):
    store = FileKnowledgeRecordStore(tmp_path)
    store.append("k1", [_entity("first")])
    store.append("k1", [_entity("second")])

    reopened = FileKnowledgeRecordStore(tmp_path)
    history = reopened.history("k1")

    assert [r.revision for r in history] == [1, 2]
    assert history[1].entities[0].payload == "second"


def test_file_store_never_overwrites_a_prior_revision_file(tmp_path):
    store = FileKnowledgeRecordStore(tmp_path)
    store.append("k1", [_entity("first")])

    revision_one_path = tmp_path / "k1" / "0001.json"
    assert revision_one_path.exists()
    original_bytes = revision_one_path.read_bytes()

    store.append("k1", [_entity("second")])

    # revision 1's file is untouched; revision 2 is a new file.
    assert revision_one_path.read_bytes() == original_bytes
    assert (tmp_path / "k1" / "0002.json").exists()


def test_file_store_retract_persists_across_instances(tmp_path):
    store = FileKnowledgeRecordStore(tmp_path)
    store.append("k1", [_entity()])
    store.retract("k1", reason="bad input")

    reopened = FileKnowledgeRecordStore(tmp_path)
    latest = reopened.latest("k1")

    assert latest is not None
    assert latest.retracted
    assert latest.retracted_reason == "bad input"


def test_file_store_keys_lists_every_directory():
    with tempfile.TemporaryDirectory() as tmp:
        store = FileKnowledgeRecordStore(tmp)
        store.append("k1", [_entity()])
        store.append("k2", [_entity()])

        assert sorted(store.keys()) == ["k1", "k2"]


def test_knowledge_record_carries_created_at_timestamp():
    store = InMemoryKnowledgeRecordStore()
    record = store.append("k1", [_entity()])

    assert isinstance(record, KnowledgeRecord)
    assert record.created_at is not None


def test_knowledge_record_is_immutable():
    store = InMemoryKnowledgeRecordStore()
    record = store.append("k1", [_entity()])

    with pytest.raises(AttributeError):
        record.retracted = True  # type: ignore[misc]
