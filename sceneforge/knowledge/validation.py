"""
SceneForge Knowledge Validation

Provides structured validation for knowledge entities, returning typed
ValidationIssue objects with severity levels. Checks cover structural
integrity (orphan scenes, self-references), data consistency (duplicate
scene indices), and temporal validity (timeline checks).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from sceneforge.knowledge.entity import Entity, EntityKind


class Severity(StrEnum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    severity: Severity
    message: str
    entity_id: UUID | None = None


def validate_entities(entities: list[Entity[object]]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    scene_entities = [e for e in entities if e.kind == EntityKind.SCENE]

    for entity in scene_entities:
        issues.extend(_check_orphan_scene(entity))
        issues.extend(_check_self_reference(entity))
        issues.extend(_check_timeline(entity))

    issues.extend(_check_duplicate_scene_indices(scene_entities))

    return issues


def _check_orphan_scene(entity: Entity[object]) -> list[ValidationIssue]:
    frame_paths = entity.metadata.get("frame_paths", [])
    if not frame_paths:
        return [
            ValidationIssue(
                severity=Severity.WARNING,
                message=f"Scene {entity.id} has no frame paths (orphan scene)",
                entity_id=entity.id,
            )
        ]
    return []


def _check_self_reference(entity: Entity[object]) -> list[ValidationIssue]:
    if entity.id in entity.parents:
        return [
            ValidationIssue(
                severity=Severity.ERROR,
                message=f"Entity {entity.id} has a self-reference in parents",
                entity_id=entity.id,
            )
        ]
    return []


def _check_timeline(entity: Entity[object]) -> list[ValidationIssue]:
    start = entity.metadata.get("start_seconds")
    end = entity.metadata.get("end_seconds")
    if start is not None and end is not None and start > end:
        return [
            ValidationIssue(
                severity=Severity.ERROR,
                message=(
                    f"Scene {entity.id} timeline inconsistency: "
                    f"start_seconds ({start}) > end_seconds ({end})"
                ),
                entity_id=entity.id,
            )
        ]
    return []


def _check_duplicate_scene_indices(
    scene_entities: list[Entity[object]],
) -> list[ValidationIssue]:
    by_media: dict[str, list[Entity[object]]] = defaultdict(list)
    for entity in scene_entities:
        media_id = entity.metadata.get("media_id")
        if media_id is not None:
            by_media[str(media_id)].append(entity)

    issues: list[ValidationIssue] = []
    for media_id, scenes in by_media.items():
        seen_indices: dict[int, Entity[object]] = {}
        for scene in scenes:
            index = scene.metadata.get("scene_index")
            if index is not None:
                idx = int(index)
                if idx in seen_indices:
                    issues.append(
                        ValidationIssue(
                            severity=Severity.ERROR,
                            message=(
                                f"Duplicate scene index {idx} in media {media_id} "
                                f"(entities {seen_indices[idx].id} and {scene.id})"
                            ),
                            entity_id=scene.id,
                        )
                    )
                else:
                    seen_indices[idx] = scene
    return issues
