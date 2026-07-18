"""
SceneForge Entity Relationship Builder (Sprint 6 spike)

The question `.ai/NEXT_TASK.md` set for Sprint 6: can entity-to-entity
relationships be represented using nothing more than the existing
`Entity` shape, before adding a graph-database dependency or a new
base type? The representation answer is yes: a relationship is just
another `Entity` (`EntityKind.RELATIONSHIP`), whose `parents` tuple
points at the two related Entity ids instead of Artifact ids, with
`metadata` carrying what the relationship means.

But building this spike surfaced a real, non-obvious finding about
the *input* shape, not the representation: `KnowledgeBuilder.build()`
is typed `list[Artifact] -> list[Entity]`. A relationship builder's
input is Entities -- the *output* of an earlier Knowledge Builder
stage (`SceneGroupingBuilder`, here) -- not Artifacts. Reusing
`KnowledgeBuilder` for this would have meant lying about the input
type or silently accepting `list[Artifact]` and never using it. So
this introduces a second, deliberately distinct Protocol,
`RelationshipBuilder`, with `relate(entities) -> list[Entity]` instead
of `build(artifacts) -> list[Entity]`. See
`docs/adr/0013-entity-relationships.md` for the full writeup.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Protocol, runtime_checkable

from sceneforge.knowledge.entity import Entity, EntityKind


@runtime_checkable
class RelationshipBuilder(Protocol):
    """
    Structural contract for turning Entities into relationship Entities.

    Deliberately not `KnowledgeBuilder`: that Protocol's `build()`
    takes `list[Artifact]`, and a relationship builder's input is
    Entities produced by an earlier Knowledge Builder stage.
    """

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    def relate(self, entities: list[Entity[Any]]) -> list[Entity[Any]]:
        """Derive relationship Entities from a collection of Entities."""
        ...


class SceneSequenceBuilder:
    """
    Links consecutive `SCENE` entities in viewing order, producing one
    `RELATIONSHIP` entity per adjacent pair ("scene N precedes scene
    N+1"), grouped by the `media_id` each scene belongs to.

    Non-`SCENE` entities are ignored rather than raising -- a
    relationship builder receiving a mixed batch (scenes, and later,
    characters or locations) should pick out what it understands and
    leave the rest for a different relationship builder, the same way
    `SceneGroupingBuilder` ignores artifacts without a `media_id`
    rather than treating them as an error.
    """

    @property
    def name(self) -> str:
        return "scene_sequence"

    @property
    def version(self) -> str:
        return "1.0.0"

    def relate(self, entities: list[Entity[Any]]) -> list[Entity[Any]]:
        scenes_by_media: dict[str, list[Entity[Any]]] = defaultdict(list)
        for entity in entities:
            if entity.kind != EntityKind.SCENE:
                continue
            media_id = entity.metadata.get("media_id")
            if media_id is None:
                continue
            scenes_by_media[media_id].append(entity)

        relationships: list[Entity[Any]] = []
        for media_id, scenes in scenes_by_media.items():
            ordered = sorted(scenes, key=lambda e: e.metadata["scene_index"])
            for earlier, later in zip(ordered, ordered[1:], strict=False):
                relationships.append(
                    Entity(
                        kind=EntityKind.RELATIONSHIP,
                        builder=self.name,
                        payload="precedes",
                        parents=(earlier.id, later.id),
                        metadata={
                            "media_id": media_id,
                            "relationship": "precedes",
                            "source_entity_id": str(earlier.id),
                            "target_entity_id": str(later.id),
                            "source_scene_index": earlier.metadata["scene_index"],
                            "target_scene_index": later.metadata["scene_index"],
                        },
                    )
                )
        return relationships
