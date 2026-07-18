# ADR 0013: Entity Relationships Reuse the Entity Shape, But Need a Separate Builder Protocol

## Status

Accepted

## Context

`.ai/NEXT_TASK.md`'s Sprint 6 question: can entity-to-entity
relationships (starting with the smallest real case — scene ordering)
be represented using nothing more than the existing `Entity` shape,
before adding a graph-database dependency or a new base type? Success
criteria required answering with a real spike, per the same discipline
ADR-0011 and ADR-0012 already established for this project.

## Decision

**Representation: yes, `Entity` already covers it.** A relationship is
just another `Entity` — `EntityKind.RELATIONSHIP` — whose `parents`
tuple points at the two related Entity ids (instead of Artifact ids,
which is what `parents` has held everywhere else so far) and whose
`metadata` carries what the relationship means (`"relationship":
"precedes"`, plus enough context to query without dereferencing the
parents). No new base type was needed. `SceneSequenceBuilder`
(`sceneforge/knowledge/relationship_builder.py`) produces these for
consecutive `SCENE` entities.

**Input shape: no, `KnowledgeBuilder` doesn't cover it, and
shouldn't.** This is the actual finding from doing the spike rather
than assuming: `KnowledgeBuilder.build()` is typed `list[Artifact] ->
list[Entity]`. A relationship builder's input is Entities — the
*output* of an earlier Knowledge Builder stage — not Artifacts.
Attempting to force `SceneSequenceBuilder` through `KnowledgeBuilder`
would have meant either lying about the input type or accepting
`list[Artifact]` and silently ignoring it. Instead, a second,
deliberately distinct Protocol exists: `RelationshipBuilder`, with
`relate(entities: list[Entity]) -> list[Entity]`.

This makes the Knowledge layer's real shape, as built, two stages:

```
Artifacts -> KnowledgeBuilder.build()      -> Entities (e.g. SceneEntity)
Entities  -> RelationshipBuilder.relate()  -> Entities (e.g. RELATIONSHIP)
```

not the one-stage `Artifacts -> Entities` the layer diagram in
`docs/architecture/LAYERS.md` originally implied.

## Consequences

- No graph-database dependency was added, and none turned out to be
  needed for the smallest real relationship case. Whether that holds
  once relationships need actual graph *queries* (not just "list every
  RELATIONSHIP entity and filter in Python," which is what
  `tests/knowledge/test_relationship_integration.py` currently does)
  is unresolved — flagged as an open question below, not assumed
  answered.
- `EntityStore` (ADR-0012) needed zero changes to persist
  `RELATIONSHIP`-kind entities — `entity_to_dict()`/`entity_from_dict()`
  are generic over any `EntityKind`, confirmed by
  `test_relationship_entity_round_trips_through_entity_store`. This is
  a point in favor of ADR-0012's decision holding up under a second
  real use, not just the first.
- `docs/architecture/LAYERS.md`'s Layer 4 description needs a note
  that Knowledge Builders now come in two Protocol shapes
  (`KnowledgeBuilder` and `RelationshipBuilder`), not one — updated
  alongside this ADR.
- A second relationship builder (e.g. "character appears in scene",
  once a face-detection provider exists) would need to consume a
  *mixed* batch of `SCENE` and `CHARACTER` entities. `RelationshipBuilder.relate()`'s
  signature already supports this (`list[Entity]`, not
  `list[SceneEntity]`); `SceneSequenceBuilder`'s own pattern of
  filtering by `kind` and ignoring what it doesn't understand is the
  established way to handle a mixed batch, demonstrated in
  `test_non_scene_entities_are_ignored`.

## Alternatives Considered

1. **Extend `KnowledgeBuilder.build()` to accept `list[Artifact] |
   list[Entity]`.** Rejected: a union input type would mean every
   implementation has to type-check its own input to know which case
   it's in, pushing a Protocol-level ambiguity into every builder
   instead of resolving it once at the Protocol boundary.
2. **A graph library (networkx or similar) from the start.** Rejected
   per `docs/philosophy/VISION.md` principle 7 — the actual first need
   (scene ordering) doesn't require graph traversal, just a sorted
   list; adding a graph dependency before a real query need existed
   would be exactly the premature-formalization mistake this project's
   Sprint 2 correction was about.
3. **A dedicated `Relationship` base type, separate from `Entity`.**
   Rejected: nothing about a relationship needs fields `Entity`
   doesn't already have (`parents` for the two endpoints, `metadata`
   for relationship-specific data, `payload` for a short label). A
   separate type would have meant a third persistence path
   (`EntityStore` already handles `Entity` generically) for no
   representational benefit.

## Open question carried forward

`test_scene_sequence_from_real_three_scene_video` currently finds
relationships by holding the whole entity list in memory and filtering
in Python. That's fine at the current scale (one movie, a handful of
scenes) and would not be fine for "find every scene a character
appears in, across a whole media library." Whether that need justifies
a real graph-query layer, or whether `EntityStore` can grow an index
(e.g. by `kind`, or by `parents` membership) without becoming a graph
database, is Sprint 7's question — not answered here, on purpose.
