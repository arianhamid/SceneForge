# ADR 0014: Relationship Querying Doesn't Need New Infrastructure Yet — Measured, Not Assumed

## Status

Accepted

## Context

Sprint 6 (ADR-0013) deliberately left one question open:
`test_scene_sequence_from_real_three_scene_video` finds relationships
by holding a three-scene entity list in memory and filtering in
Python. `.ai/NEXT_TASK.md`'s Sprint 7 objective was to find out whether
that approach holds up at a realistic scale, or whether `EntityStore`
needs an index, a different backend, or a real graph library — by
building a real spike large enough to actually expose a limit if one
exists, not by guessing.

The first thing the spike found, before any performance question even
came up: **`EntityStore` had no way to enumerate what it contained.**
`get`/`put`/`has`/`delete` all require knowing the exact key in
advance. `entity_build_key()` is derived from the exact set of input
artifact ids — which means answering "what relationships exist for
this scene" was, before this ADR, not slow, but *impossible*: there
was no way to ask "what's in here" at all, only "is this specific
thing in here."

## Decision

Added `keys() -> list[str]` to the `EntityStore` Protocol and both
implementations (`FileEntityStore`, `InMemoryEntityStore`), plus two
query primitives built on top of it
(`sceneforge/knowledge/storage.py`):

- `iter_all_entities(store)` — enumerate every stored key, fetch,
  flatten. The naive full-scan primitive everything else is built on.
- `find_related(store, entity_id)` — every Entity whose `parents`
  include `entity_id`. The concrete query this spike exists to answer.

Then measured `find_related()` against a synthetic dataset sized like
a modest real library — 300 movies × 20 scenes = 11,700 entities
across 600 `FileEntityStore` keys (real disk I/O, not
`InMemoryEntityStore`) — searching for a scene buried in the middle of
the dataset, not the first or last record.

**Result: 0.125 seconds.** (See
`tests/knowledge/test_query_spike.py::test_find_related_completes_in_reasonable_time_at_scale`,
which asserts a generous 5-second bound and prints the actual number.)

**Conclusion: no index, no new backend, no graph library — yet.** A
full linear scan over thousands of entities, reading real JSON files
off disk, answers a real relationship query in well under a second.
Building query infrastructure now would have been solving a problem
that doesn't exist at any scale this project has evidence for.

## Consequences

- Sprint 7's success criterion is met with a real number, not an
  assumption: `.ai/NEXT_TASK.md`'s open item ("attempted against
  `EntityStore` as it exists today, and either succeeded... or
  failed") succeeded, measured at 300-movie scale.
- `iter_all_entities()`/`find_related()` are now the established
  pattern for querying entities. Future query needs (find every scene
  a character appears in, once that capability exists) should extend
  this pattern — filter predicates over `iter_all_entities()` — rather
  than reaching for new infrastructure, until a real measurement shows
  linear scan isn't enough.
- This measurement is valid at *this* scale (hundreds of movies,
  thousands of entities) and says nothing about ten thousand movies or
  a million entities. The test's docstring and the 5-second assertion
  bound are deliberately explicit that this is evidence for *now*, not
  a permanent guarantee — if `find_related()` ever approaches that
  bound in practice, that itself is the signal to revisit this
  decision, not a reason to quietly raise the bound.
- `ArtifactStore` (`sceneforge/core/storage.py`, ADR-0008) still has
  no equivalent `keys()`/enumeration method. Not needed by anything
  real yet — Providers are looked up by exact `content_key()`, not
  queried — but noted here so a future Sprint doesn't have to
  rediscover this asymmetry from scratch if a similar need arises
  there.

## Alternatives Considered

1. **Add a real index (e.g. a `media_id -> keys` or `entity_id ->
   keys` mapping maintained alongside writes) before measuring
   whether one's needed.** Rejected — this is exactly the
   premature-formalization pattern every prior ADR in this series
   (0011, 0012, 0013) was written to avoid repeating. The measurement
   came first this time too, and it didn't ask for one.
2. **A real graph library (networkx or similar).** Rejected for the
   same reason as ADR-0013's alternative #2, now with an actual
   number behind the rejection instead of just a principle.
3. **Don't measure at all — assume linear scan is "obviously fine" at
   small scale and move on.** Rejected: "obviously fine" was also the
   assumption `EntityStore` having no `keys()` method violated. The
   whole point of this ADR series is not trusting assumptions that are
   cheap to actually check.
