"""Tests for knowledge validation module."""

from uuid import uuid4

import pytest

from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.validation import (
    Severity,
    ValidationIssue,
    validate_entities,
)


def test_empty_entities_returns_no_issues():
    issues = validate_entities([])
    assert issues == []


def test_non_scene_entities_return_no_issues():
    entity = Entity(kind=EntityKind.CHARACTER, builder="test")
    issues = validate_entities([entity])
    assert issues == []


def test_orphan_scene_returns_warning():
    entity = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        metadata={"frame_paths": [], "media_id": str(uuid4()), "scene_index": 0},
    )
    issues = validate_entities([entity])
    assert len(issues) == 1
    assert issues[0].severity == Severity.WARNING
    assert issues[0].entity_id == entity.id
    assert "orphan" in issues[0].message.lower()


def test_scene_with_frames_no_orphan_issue():
    entity = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        metadata={
            "frame_paths": ["/path/to/frame.jpg"],
            "media_id": str(uuid4()),
            "scene_index": 0,
        },
    )
    issues = validate_entities([entity])
    assert issues == []


def test_no_self_references_returns_no_issues():
    entity_id = uuid4()
    entity = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        id=entity_id,
        parents=(uuid4(), uuid4()),
        metadata={
            "frame_paths": ["/frame.jpg"],
            "media_id": str(uuid4()),
            "scene_index": 0,
        },
    )
    issues = validate_entities([entity])
    assert issues == []


def test_self_reference_returns_issue():
    entity_id = uuid4()
    entity = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        id=entity_id,
        parents=(entity_id, uuid4()),
        metadata={
            "frame_paths": ["/frame.jpg"],
            "media_id": str(uuid4()),
            "scene_index": 0,
        },
    )
    issues = validate_entities([entity])
    assert len(issues) == 1
    assert issues[0].severity == Severity.ERROR
    assert issues[0].entity_id == entity_id
    assert "self-reference" in issues[0].message.lower()


def test_duplicate_scene_indices_returns_error():
    media_id = uuid4()
    entity1 = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        metadata={
            "frame_paths": ["/frame1.jpg"],
            "media_id": str(media_id),
            "scene_index": 0,
        },
    )
    entity2 = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        metadata={
            "frame_paths": ["/frame2.jpg"],
            "media_id": str(media_id),
            "scene_index": 0,
        },
    )
    issues = validate_entities([entity1, entity2])
    assert len(issues) == 1
    assert issues[0].severity == Severity.ERROR
    assert "duplicate" in issues[0].message.lower()


def test_different_media_same_scene_index_no_issue():
    entity1 = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        metadata={
            "frame_paths": ["/frame1.jpg"],
            "media_id": str(uuid4()),
            "scene_index": 0,
        },
    )
    entity2 = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        metadata={
            "frame_paths": ["/frame2.jpg"],
            "media_id": str(uuid4()),
            "scene_index": 0,
        },
    )
    issues = validate_entities([entity1, entity2])
    assert issues == []


def test_timeline_consistency_no_issue():
    entity = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        metadata={
            "frame_paths": ["/frame.jpg"],
            "media_id": str(uuid4()),
            "scene_index": 0,
            "start_seconds": 0.0,
            "end_seconds": 10.0,
        },
    )
    issues = validate_entities([entity])
    assert issues == []


def test_timeline_inconsistency_returns_error():
    entity = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        metadata={
            "frame_paths": ["/frame.jpg"],
            "media_id": str(uuid4()),
            "scene_index": 0,
            "start_seconds": 10.0,
            "end_seconds": 5.0,
        },
    )
    issues = validate_entities([entity])
    assert len(issues) == 1
    assert issues[0].severity == Severity.ERROR
    assert issues[0].entity_id == entity.id
    msg = issues[0].message.lower()
    assert "start" in msg or "timeline" in msg


def test_timeline_equal_no_issue():
    entity = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        metadata={
            "frame_paths": ["/frame.jpg"],
            "media_id": str(uuid4()),
            "scene_index": 0,
            "start_seconds": 5.0,
            "end_seconds": 5.0,
        },
    )
    issues = validate_entities([entity])
    assert issues == []


def test_validation_issue_is_frozen_dataclass():
    issue = ValidationIssue(
        severity=Severity.WARNING,
        message="test",
        entity_id=uuid4(),
    )
    assert issue.severity == Severity.WARNING
    assert issue.message == "test"
    with pytest.raises(AttributeError):
        issue.message = "changed"  # type: ignore[misc]


def test_multiple_issues_from_multiple_entities():
    media_id = uuid4()
    orphan = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        metadata={"frame_paths": [], "media_id": str(media_id), "scene_index": 0},
    )
    bad_timeline = Entity(
        kind=EntityKind.SCENE,
        builder="test",
        metadata={
            "frame_paths": ["/frame.jpg"],
            "media_id": str(media_id),
            "scene_index": 1,
            "start_seconds": 20.0,
            "end_seconds": 10.0,
        },
    )
    issues = validate_entities([orphan, bad_timeline])
    severities = {i.severity for i in issues}
    assert Severity.WARNING in severities
    assert Severity.ERROR in severities
