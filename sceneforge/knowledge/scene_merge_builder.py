"""
SceneForge Scene Merge Builder

The Sprint 10 spike: `SceneGroupingBuilder` and `SceneFaceBuilder` each
produce their own `EntityKind.SCENE` entity for the same logical scene
(same `media_id` + `scene_index`) on the same video. Does combining
them need a new persistence or query concept in Layer 5, or does the
existing `RelationshipBuilder` shape (`Entity -> Entity`, ADR-0013)
already cover it?

It does. `SceneMergeBuilder` is a `RelationshipBuilder` -- same
Protocol as `SceneSequenceBuilder` -- whose `relate()` groups incoming
`SCENE` entities by `(media_id, scene_index)` and, wherever more than
one builder contributed an entity for the same key, produces a single
combined `SCENE` entity. Each source builder's own metadata and
payload are kept under a key namespaced by that builder's `name`, so
combining a third or fourth builder's output later needs no special
casing and no risk of two builders silently overwriting each other's
same-named metadata field.

No new base type, no new Protocol, no new persistence concept. See
`docs/adr/0018-scene-merge-builder.md`.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from sceneforge.knowledge.entity import Entity, EntityKind


class SceneMergeBuilder:
    """
    Merges `SCENE` entities from different builders that describe the
    same `(media_id, scene_index)` into one combined entity.

    Entities with no `media_id`/`scene_index` in metadata, or that are
    the *only* entity for their key (nothing to merge with), are left
    out of the output -- this builder produces exactly the merged
    records, not a passthrough of everything it saw.
    """

    @property
    def name(self) -> str:
        return "scene_merge"

    @property
    def version(self) -> str:
        return "1.0.0"

    def relate(self, entities: list[Entity[Any]]) -> list[Entity[Any]]:
        by_key: dict[tuple[str, int], list[Entity[Any]]] = defaultdict(list)
        for entity in entities:
            if entity.kind != EntityKind.SCENE:
                continue
            media_id = entity.metadata.get("media_id")
            scene_index = entity.metadata.get("scene_index")
            if media_id is None or scene_index is None:
                continue
            by_key[(media_id, scene_index)].append(entity)

        merged: list[Entity[Any]] = []
        for (media_id, scene_index), group in by_key.items():
            if len(group) < 2:
                continue  # nothing to merge -- only one builder contributed

            combined_metadata: dict[str, Any] = {
                "media_id": media_id,
                "scene_index": scene_index,
                "merged_from": sorted({e.builder for e in group}),
            }
            for source in group:
                combined_metadata[source.builder] = {
                    **{k: v for k, v in source.metadata.items()},
                    "payload": source.payload,
                }

            merged.append(
                Entity(
                    kind=EntityKind.SCENE,
                    builder=self.name,
                    parents=tuple(e.id for e in group),
                    metadata=combined_metadata,
                )
            )
        return merged
