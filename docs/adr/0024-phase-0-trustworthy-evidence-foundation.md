# ADR-0024: Phase 0 — Trustworthy Identity, Evidence, and Run Provenance

## Status

Accepted

## Context

[`docs/research/2026-07-21-comprehensive-movie-understanding-architecture.md`](../research/2026-07-21-comprehensive-movie-understanding-architecture.md)
proposed a long-term direction built on being able to trace every conclusion
back to durable evidence, distinguish observation from interpretation, and
know exactly which input and configuration produced a result. The follow-up
[`docs/research/2026-07-22-comprehensive-movie-understanding-implementation-review.md`](../research/2026-07-22-comprehensive-movie-understanding-implementation-review.md)
checked that assumption against the current repository rather than the
architecture documents, and reproduced four concrete defects live, not as
speculative risk:

1. `Media.id` is a random `uuid4()` assigned on every load
   ([`media/base.py`](../../sceneforge/media/base.py)). `content_key()`
   ([`core/storage.py`](../../sceneforge/core/storage.py)) hashes
   `name:id:provider:version` only. Reloading the same unchanged file
   produces a different cache key (false miss); running two configurations
   of the same provider against one `Media` object produces the *same* key
   (false hit, silently wrong cached artifact returned).
2. `Entity.provenance` ([`knowledge/entity.py`](../../sceneforge/knowledge/entity.py))
   could not be persisted: `FileEntityStore.put()` raised
   `TypeError: Object of type Provenance is not JSON serializable` for any
   `Entity` carrying a real `Provenance`, confirmed by direct reproduction.
   No production builder populates it today, so this had gone unnoticed.
3. Nothing lets an application resolve a conclusion back to the evidence
   that supports it: `Artifact` carries no required source/interval/anchor
   fields, `Entity.parents` is an untyped `UUID` tuple whose meaning
   depends on which builder produced it, and `ArtifactStore` has no lookup
   by artifact ID, media, or time.
4. `MappingProxyType` on `Artifact`/`Entity` protects only the outer
   metadata mapping; nested lists and dicts (frame lists, face maps) remain
   mutable in place, confirmed by direct reproduction. The same JSON store
   is also used, without distinction, as both an evictable computation
   cache (supports overwrite/delete) and an implied durable evidence
   record.

Every phase in the 2026-07-21 research document's roadmap — Facts, Events,
external verification, interpretation, forecasting, the final report — is
written as if "this cache key means this exact input and configuration,"
"this record says why the system believes it," and "this claim traces back
to durable evidence" already hold. They do not.

## Decision

Insert a **Phase 0** before the previously planned Phase 1 (a real
captioning or object-detection provider, per `NEXT_TASK.md`). Phase 0 has
five parts. Each ships as its own reviewed, tested change; the next part
does not start until the previous one has tests proving it, matching this
project's existing "prove it before you formalize it" discipline applied at
Phase-0 granularity rather than only at the phase level.

1. **Provenance round-trips through `EntityStore`.** Shipped alongside this
   ADR: `_serialize_value`/`entity_from_dict` in
   [`knowledge/storage.py`](../../sceneforge/knowledge/storage.py) now
   convert `Provenance` to and from a plain JSON-safe mapping, with
   regression tests (`tests/knowledge/test_storage.py`,
   `test_entity_provenance_round_trips_through_dict`,
   `test_file_entity_store_persists_entity_with_provenance`) covering both
   the dict codec directly and the real file-backed store — the exact path
   the implementation review used to reproduce the failure.

2. **Content identity plus an execution fingerprint**, replacing the single
   random `Media.id` currently used in `content_key()`:
   - *Content identity*: derived from file bytes (or a documented
     normalized-asset hash where byte-identity is not the right notion),
     not a random UUID. Two loads of the same unchanged file must resolve
     to the same content identity.
   - *Edition identity*: reserved as an initially unresolved/opaque field for
     the logical work and specific cut (theatrical, extended, regional, etc.).
     It belongs in provenance, run scope, and queries, but does not enter the
     computation-cache key merely because external matching later resolves or
     corrects it. A provider includes edition-derived information in its
     execution fingerprint only when that information actually changes the
     computation. Populating edition identity automatically remains Phase 4's
     concern.
   - *Execution fingerprint*: provider implementation and schema version,
     model ID/revision (and weights hash where feasible), prompt/template
     version, sampling/preprocessing/inference configuration, and relevant
     tool/library versions — exposed through a deterministic provider
     execution descriptor and folded into `content_key()` alongside provider
     name and version. Secrets and incidental process state never enter this
     descriptor.
   - `Media.evolve()` preserves content identity when it only adds or corrects
     descriptive metadata for the same underlying bytes. Changing the source
     bytes or creating a transformed derivative requires a new content
     identity. Any evolved value that changes provider behavior belongs in the
     provider's execution fingerprint; descriptive values that do not affect
     output do not invalidate the computation cache.
   - This is a breaking, cache-invalidating change to `content_key()`. That
     is accepted deliberately: the current key quietly conflates
     configurations that must not collide and quietly misses reloads that
     should hit. There is no real cached corpus in production to migrate,
     so no migration tooling is being built for it — existing local caches
     are simply invalidated.
   - **This item is decided here, not implemented here.** It changes a
     stable, exercised contract (`content_key()`, `ArtifactStore`) touched
     by every existing provider and test, and needs its own follow-on
     change and test pass rather than riding in on this ADR.

3. **A minimal typed evidence contract**: an `EvidenceAnchor` (edition,
   stream, presentation interval or point, optional spatial region, durable
   asset reference) and an `EvidenceLink`, plus artifact lookup by ID and,
   at minimum, by media. An `EvidenceLink`'s `source`/`target` are not bare
   UUIDs — each is a `(kind, id)` pair (`kind` distinguishing at least
   `artifact`, `entity`, `external_claim`, and `revision`), because a raw
   UUID's meaning already varies by builder in the current `Entity.parents`
   field, and repeating that ambiguity in the new evidence contract would
   reproduce the exact problem this ADR exists to fix. `relation` is typed,
   e.g. `supports`/`derived_from`. No graph database — an indexed or
   SQLite-backed spike is sufficient, consistent with the standing rule in
   ADR-0014, ADR-0019, and ADR-0021 that a dedicated graph backend waits
   for a measured query that plain iteration cannot answer.

4. **Separate the cache role from the evidence role.** `FileArtifactStore`
   and `FileEntityStore` remain a legitimate evictable, overwritable
   computation cache. A durable, append-oriented evidence/knowledge record
   concept — with explicit revision and supersession semantics — is a
   distinct thing, even if it is initially backed by the same file format.
   Conflating the two today means correcting an earlier result and evicting
   a stale cache entry look identical, which the research document's
   evidence-permanence requirement does not allow.

5. **A minimal `AnalysisRun` manifest** recording, per stage: provider,
   model, and configuration versions; which intervals/modalities were
   attempted, skipped, or failed; and whether each result was a cache hit
   or a fresh run. This is the smallest artifact that lets a report later
   compute real coverage instead of inferring it from whichever outputs
   happen to exist.

**Explicitly deferred, not forgotten:** provider-neutral artifact contracts
(interchangeable captioners/object-detectors; the Runtime decoding-boundary
honesty gap). Normalizing an interface from a single real implementation is
the speculative abstraction this project has consistently avoided (see the
pattern behind ADR-0011, ADR-0016, ADR-0018: build the second real case,
then extract the shared shape). These are revisited once the Phase 1
captioning/object-detection provider supplies that second concrete case,
   not before a second implementation of the same normalized capability gives
   the abstraction two real cases to fit. The first Phase-1 caption/object
   provider may define its concrete output without claiming interchangeability.

**Also explicitly deferred:** deep immutability of nested `Artifact`/`Entity`
payloads. `MappingProxyType` currently protects only the outer metadata
mapping; a nested list or dict (a frame list, a face map) can still be
mutated in place, confirmed by direct reproduction. This is a real defect,
but item 4 above (separating the evictable cache from durable evidence) does
not fix it by itself, and fixing it generally means either recursively
freezing arbitrary nested structures or moving to typed frozen payloads —
   both are more naturally sized with the first typed Fact payload rather than
   by recursively freezing today's loosely-typed `dict[str, Any]` metadata
   blobs in place. The first Fact cannot be declared production-ready until its
   own typed payload is deeply immutable. This remains tracked in
   `PROJECT_STATE.md` rather than being conflated with item 4.

## Consequences

- This ADR amends the caching-identity portion of
  [ADR-0008](0008-artifact-persistence.md): `content_key()`'s basis of
  "media identity + provider name + provider version" is superseded by item
  2's content identity plus execution fingerprint once that item ships.
  Edition identity remains provenance/query scope unless a computation
  explicitly consumes it. ADR-0008's `ArtifactStore`/`FileArtifactStore`/
  `InMemoryArtifactStore` protocol and persistence design are unaffected and
  remain in force — only the key basis changes.
- ADR-0008's open question ("what should `Media.evolve()` mean for cache
  invalidation across multiple enrichers?", tracked as an Open RFC in
  `PROJECT_STATE.md`) is resolved by item 2: metadata-only evolution of the
  same bytes preserves content identity; new or transformed bytes require a
  new identity; output-affecting evolved values participate in the execution
  fingerprint. The implementation must enforce this decision, but the
  architectural question is no longer open.
- Phase 1 (the captioning/object-detection provider named in
  `NEXT_TASK.md`) does not start until Phase 0 items 2–5 are real and
  tested. This delays the previously announced next task, but avoids
  building the first Fact on an identity and evidence foundation already
  known, by direct reproduction, to be unsound.
- `content_key()`'s change is breaking. Every existing provider and its
  tests will need updating when that follow-on change lands; this is
  tracked as a separate task from this ADR.
- The evidence-anchor/lookup work and the cache/evidence split add new
  types but stay index-only, consistent with the project's standing
  anti-graph-database rule.
- `NEXT_TASK.md` and `PROJECT_STATE.md` should be updated to reflect Phase
  0 as the current objective in place of the captioning/object-detection
  provider, and to record that `Entity.provenance` now round-trips.

## Alternatives Considered

1. **Build the captioning/object-detection provider first**, per the
   original `NEXT_TASK.md` order, and fix identity/evidence issues
   opportunistically as they are hit. Rejected: the implementation review
   reproduced these as live bugs today, not speculative future risk, and
   every phase in the 2026-07-21 research document depends on results
   being traceable to durable evidence. Building Facts on a cache that can
   silently collide or silently miss would make results non-reproducible
   from day one — cheaper to fix now than to unwind after Events, State,
   and reasoning are built on top of it.
2. **Fix all five Phase-0 items in one large change.** Rejected: the items
   have different risk profiles — provenance is a contained bugfix behind
   existing types; identity is a breaking key-format change; evidence
   anchors are new types; the run manifest is a new concept — and bundling
   them would make each harder to review and to roll back independently.
3. **Design and ship the full "target conceptual records" from the
   2026-07-21 research document now** (atomic assertion, event/state,
   interpretation dossier, forecast record). Rejected: most of those types
   have no real producer yet. Phase 0 only needs the general capability to
   trace a conclusion back to its source evidence, matching the project's
   standing rule against building types ahead of a real consumer — the
   same rule ADR-0021 already applied to the rest of the Understanding
   Ladder.
