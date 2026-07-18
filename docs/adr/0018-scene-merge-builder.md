# ADR 0018: Cross-Builder Entity Merging Reuses RelationshipBuilder — No New Persistence Concept Needed

## Status

Accepted

## Context

Sprint 9 closed with a real observation: `SceneGroupingBuilder` and
`SceneFaceBuilder` each produce their own `EntityKind.SCENE` entity
for the same logical scene (same `media_id` + `scene_index`) on the
same video, and nothing merges them. `.ai/NEXT_TASK.md`'s Sprint 10
question was whether Layer 5 (Knowledge Graph) needs a real
entity-merge concept to handle this — a new base type, a new
persistence mechanism, a new query capability — or whether something
already in the framework covers it, to be found out with a real spike
using both builders' actual output rather than decided on paper.

## Decision

**No new concept.** `SceneMergeBuilder` is a `RelationshipBuilder` —
the exact same Protocol `SceneSequenceBuilder` already uses
(`relate(entities: list[Entity]) -> list[Entity]`, ADR-0013). It
groups incoming `SCENE` entities by `(media_id, scene_index)` and,
wherever more than one builder contributed an entity for the same key,
produces one combined entity. Each source builder's metadata and
payload are kept under a key namespaced by that builder's `name`
(`combined.metadata["scene_grouping"]`, `combined.metadata["scene_face"]`),
so a third or fourth builder's output merges in later with zero risk
of two builders silently overwriting each other's same-named field —
proven directly in `test_three_builders_merge_into_one_entity`.

`RelationshipBuilder` was originally built (ADR-0013) for linking two
*different* entities (scene N precedes scene N+1). This is the same
Protocol used for a different relationship: "these entities describe
the same thing." Nothing about the Protocol's shape assumed one
relationship type over the other — it just turned out to fit both.

## Consequences

- Proven against real data, not just the hand-built fixtures in
  `tests/knowledge/test_scene_merge_builder.py`:
  `tests/knowledge/test_scene_merge_integration.py` runs real
  `SceneGroupingBuilder` and `SceneFaceBuilder` output (itself built
  from real `ffmpeg`/`scenedetect`/`opencv` calls) through
  `SceneMergeBuilder`, confirming both builders agree on real scene
  boundaries (`start_seconds`/`end_seconds` match exactly across the
  two independently-computed entities) — real evidence the
  `(media_id, scene_index)` correlation key is trustworthy, not just
  assumed to be.
- `EntityStore` (ADR-0012) and the query primitives (ADR-0014) needed
  zero changes — `SceneMergeBuilder`'s output is a plain `Entity`, so
  it persists and queries exactly like every other entity kind.
- This is the third time (after ADR-0011's builder scope and
  ADR-0016's cross-domain correlation) that checking whether an
  existing shape already covers a new need found that it did, once
  actually tried. Worth naming as a pattern in
  `docs/guides/ADDING_A_PROVIDER.md`'s sibling guidance for future
  Knowledge Builder authors: check `KnowledgeBuilder` and
  `RelationshipBuilder` against the actual need before assuming a
  third shape is required.
- An entity produced by only one builder (nothing to merge with) is
  correctly left unmerged rather than passed through — `SceneMergeBuilder`
  produces exactly the merged records, not a copy of everything it saw.
  A caller wanting "every scene, merged where possible, standalone
  otherwise" combines this builder's output with the original
  unmerged entities, the same compositional pattern
  `examples/end_to_end/analyze_video.py` already uses for chaining
  builders.

## Alternatives Considered

1. **A new `MergedEntity` type or a `merge()` method on `Entity`
   itself.** Rejected: nothing about merging needs a new base type —
   `Entity`'s existing `metadata` (a free-form mapping) and `parents`
   (tracing back to sources) already had everything a merge record
   needs.
2. **Namespace-free metadata merging (later builder's keys silently
   overwrite earlier ones for same-named fields).** Rejected once
   actually building it made the risk concrete: `SceneGroupingBuilder`
   and `SceneFaceBuilder` don't currently collide on any metadata key
   name, but nothing guarantees a future third builder wouldn't, and
   namespacing costs nothing to add now versus discovering a silent
   data-loss bug later.
3. **Push merging into `EntityStore` itself** (a `put()` that merges
   with any existing entry at the same logical key instead of
   creating build-key-scoped cache entries). Rejected: conflates two
   different concerns — `EntityStore` is a cache keyed by exact build
   input (ADR-0012), and merging is a domain operation over already-
   built entities. Keeping them separate means `EntityStore`'s cache
   semantics stay simple and predictable.
