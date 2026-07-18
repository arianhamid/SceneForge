# ADR 0012: Entity Persistence Is a Separate EntityStore, Not a Shared Generic with ArtifactStore

## Status

Accepted

## Context

`.ai/PROJECT_STATE.md` flagged this as the top open RFC after Sprint 4:
`SceneGroupingBuilder` produces `Entity` objects that live only in
memory for the duration of a script run. `ArtifactStore` (ADR-0008)
already solved an almost identical problem for `Artifact`. The
question was whether to extend `ArtifactStore` to cover `Entity` too,
or build something separate — and per `.ai/NEXT_TASK.md`'s explicit
instruction, to answer with a real spike rather than a design doc.

The spike (`sceneforge/knowledge/storage.py`,
`tests/knowledge/test_storage.py`) built both directions far enough to
compare them concretely.

## Decision

**A separate `EntityStore`, structurally parallel to `ArtifactStore`
but not sharing a generic implementation with it.**

What turned out to be identical: the JSON-serialization mechanics.
`Entity` and `Artifact` are both flat, frozen dataclasses with a UUID
`id`, a kind enum, a `MappingProxyType` metadata field, and a
`parents` tuple, so `entity_to_dict()`/`entity_from_dict()` in
`sceneforge/knowledge/storage.py` are near-line-for-line the same
generic `dataclasses.fields()`-based approach as `artifact_to_dict()`/
`artifact_from_dict()`.

What turned out to genuinely differ, and is why a shared `Store[T]`
generic was rejected once actually attempted:

1. **Field names don't align.** `Artifact.provider` vs.
   `Entity.builder` — same *role* (who produced this), different name,
   because "provider" and "builder" are already the established
   vocabulary in their respective layers (`docs/GLOSSARY.md`). A shared
   generic would have needed to pick one name and lose the other's
   clarity, or add an indirection layer neither type actually needs on
   its own.
2. **The cache-key basis is structurally different, not just
   named differently.** `content_key()` (Artifact) is keyed on *one*
   media object's identity plus *one* provider. `entity_build_key()`
   (Entity) is keyed on the exact *set* of input artifact ids plus one
   builder — because `SceneGroupingBuilder.build()` legitimately
   synthesizes entities from a batch spanning several media objects at
   once (it does its own internal `by_media_id` grouping). Trying to
   force Entity's key through Artifact's single-media shape, or vice
   versa, would have meant lying about what either key actually means.

A small orchestration helper, `build_with_cache()`
(`sceneforge/knowledge/builder.py`), plays `Pipeline`'s cache-check/
cache-write role for Knowledge Builders — but is a plain function, not
a class. There's no evidence yet that Knowledge Builders need
`Pipeline`'s other responsibilities (retries, timeouts, cancellation,
enrichment): a builder is a synchronous, pure transform over data
already in memory, not a call to a slow or flaky external system. See
"Alternatives Considered" below.

## Consequences

- `Entity` persistence is now real and tested
  (`FileEntityStore`/`InMemoryEntityStore`,
  `tests/knowledge/test_storage.py`), closing the top item from
  `.ai/PROJECT_STATE.md`'s Sprint 4 open RFCs.
- `register_entity_type()` mirrors `register_artifact_type()`
  (ADR-0008) for exact round-tripping of future `Entity` subclasses
  (a `CharacterEntity`, a `LocationEntity`) — proven in
  `test_register_entity_type_enables_exact_roundtrip`.
- Two parallel storage modules (`sceneforge/core/storage.py`,
  `sceneforge/knowledge/storage.py`) now exist with near-identical
  serialization internals. This is duplication, accepted deliberately:
  the alternative (one generic module both layers import from) was
  tried in the spike and rejected per the field-name and cache-key
  reasons above. If a *third* layer ever needs the same
  serialize-a-frozen-dataclass-to-JSON pattern, that's the point to
  reconsider extracting the shared 80% into a private helper — not
  before, and not by guessing what the third case needs today.
- `build_with_cache()` deliberately doesn't try to be `Pipeline` for
  Knowledge Builders. If a second Knowledge Builder later needs
  retries or async execution, that's real evidence to design against —
  building it now would repeat the exact mistake ADR-0011 was written
  to avoid one layer down.

## Alternatives Considered

1. **A generic `Store[T]` shared by `ArtifactStore` and `EntityStore`.**
   Attempted in the spike; abandoned once the field-name and cache-key
   differences above became concrete rather than hypothetical. The
   generic would have worked syntactically (both types round-trip via
   `dataclasses.fields()`) but would have papered over a real semantic
   difference in what the two cache keys mean.
2. **Store `Entity` objects inside `ArtifactStore` by treating them as
   a kind of Artifact.** Rejected: `EntityKind` and `ArtifactKind` are
   deliberately separate vocabularies (`docs/GLOSSARY.md` distinguishes
   Artifact = single-provider observation from Entity = cross-artifact
   synthesis); conflating them at the storage layer would blur a
   distinction the domain model draws on purpose.
3. **A full `KnowledgeBuilderPipeline` class, mirroring `Pipeline`
   exactly** (retries, timeouts, `ProcessingContext`). Rejected for
   now per the "Consequences" section above — no real Knowledge
   Builder has demonstrated needing any of that machinery yet.
