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
   random `Media.id` currently used in `content_key()`. **Shipped**,
   narrower than originally decided here — see below for what's real and
   what's still open:
   - *Content identity*: **shipped.**
     [`media_content_identity()`](../../sceneforge/core/storage.py) hashes
     real file bytes when `metadata["source"]` is set and resolves to a
     file on disk; otherwise it falls back to a documented, deterministic
     hash of `media.name` (synthetic/in-memory media with no backing
     file — mirrors `MediaHashProvider`'s existing two-tier strategy
     rather than importing it, since Core cannot depend on `contrib`).
     Verified directly: two separate loads of the same unchanged file now
     produce the same `content_key()`; two different files produce
     different keys.
   - *Edition identity*: **not shipped, deferred further.** The original
     plan reserved an unresolved/opaque field on `Media` for the logical
     work and cut. On implementation, adding that field now would mean
     adding a speculative field to a stable, heavily used dataclass with
     zero real consumers — exactly the pattern this project's standing
     rule exists to prevent (the same reasoning as Alternative 3 below).
     Revisit when Phase 4 (external identity/context) has a real
     consumer for it, not before.
   - *Execution fingerprint*: **shipped, as a string, not a structured
     descriptor.** `Provider.execution_fingerprint` is a new property
     (concrete default `""` on the ABC in
     [`core/provider.py`](../../sceneforge/core/provider.py), and on the
     structural `Provider`/`AsyncProvider` protocols) that a provider
     overrides when its constructor-time configuration changes output.
     `WhisperTranscribeProvider` overrides it with a hash of its
     `transcribe_kwargs` — the concrete case the implementation review
     reproduced live (two differently configured instances colliding
     under the old key). Folded into `content_key()` as a fourth
     parameter, defaulting to `""` for backward compatibility. A fully
     structured descriptor (separate model-ID, prompt-version,
     tool-version fields rather than one opaque string) is deferred until
     a second provider actually needs to distinguish those dimensions
     independently — one real case (Whisper) does not yet justify the
     structure.
   - `Media.evolve()`'s interaction with content identity: **not
     separately tested.** Content identity depends only on
     `metadata["source"]` and `media.name`, neither of which a typical
     metadata-only `evolve()` call changes, so the stated rule
     ("metadata-only evolution preserves identity, changed bytes don't")
     holds by construction today. No dedicated regression test exists yet
     for the case where `evolve()` itself changes `source`.
   - This was a breaking, cache-invalidating change to `content_key()`,
     as accepted. Every call site (`Pipeline`, `AsyncPipeline`) and every
     test constructing a `content_key()` by hand were updated; no
     migration tooling was built, per the original decision.
   - Also required, not anticipated in the original decision: the
     structural `Provider` protocol
     ([`core/provider_protocol.py`](../../sceneforge/core/provider_protocol.py))
     and `AsyncProvider` protocol
     ([`core/async_provider.py`](../../sceneforge/core/async_provider.py))
     both needed the new property added explicitly — these are separate
     from the `Provider` ABC contrib providers subclass, and Pipeline
     type-checks against the structural one. Every duck-typed test fixture
     satisfying either protocol needed updating too (three fixtures now
     subclass the ABC instead of hand-duplicating its shape, matching how
     real contrib providers already do it).

3. **A minimal typed evidence contract.** **Shipped.**
   [`EvidenceAnchor`](../../sceneforge/core/evidence.py) (media, stream,
   presentation interval or point, optional spatial region, durable asset
   reference, reserved edition-identity field) and
   [`EvidenceLink`](../../sceneforge/core/evidence.py), plus artifact
   lookup by ID (`find_artifact_by_id()`) and by media
   (`find_artifacts_by_media()`) in
   [`core/storage.py`](../../sceneforge/core/storage.py), built on a new
   `ArtifactStore.keys()` (the enumeration method `EntityStore` already
   had, per ADR-0014 — previously the one asymmetry between the two
   stores). An `EvidenceLink`'s `source`/`target` are `Reference`
   `(kind, id)` pairs, not bare UUIDs — `kind` distinguishes `artifact`,
   `entity`, `external_claim`, and `revision` — because a raw UUID's
   meaning already varies by builder in the current `Entity.parents`
   field, and repeating that ambiguity in the new evidence contract would
   reproduce the exact problem this ADR exists to fix. `relation` is
   typed: `supports`/`derived_from` only, the two named explicitly here —
   more relations are added only when a real builder needs one, not
   speculatively. No graph database — the lookup is naive iteration over
   `ArtifactStore.keys()`, consistent with the standing rule in
   ADR-0014, ADR-0019, and ADR-0021 that a dedicated graph backend waits
   for a measured query that plain iteration cannot answer.

   **Not shipped, deliberately:** persistence for `EvidenceAnchor`/
   `EvidenceLink` themselves. No builder produces either type yet, so
   adding JSON round-trip support now (the same fix `Provenance` needed
   in item 1) would be solving a problem with no real caller — add it
   when a real Fact/Event builder needs to store one, matching this
   project's standing rule against building ahead of a real consumer.

4. **Separate the cache role from the evidence role.** **Shipped.**
   `FileArtifactStore` and `FileEntityStore` are unchanged — they remain
   the legitimate evictable, overwritable computation cache.
   [`KnowledgeRecordStore`](../../sceneforge/knowledge/storage.py) (with
   `FileKnowledgeRecordStore` and `InMemoryKnowledgeRecordStore`
   implementations) is the distinct durable, append-only counterpart:
   `append()` always creates a new numbered revision file and never
   overwrites or deletes one; there is no `put`/`delete` on this store on
   purpose. `retract()` records that a conclusion is withdrawn as a new,
   dated revision rather than erasing the original — "we no longer
   believe this" is itself a durable fact, not a silent disappearance.
   Initially backed by the same JSON-per-file format as `FileEntityStore`,
   as the ADR anticipated — the roles are what changed, not (yet) the
   storage technology. No builder produces `KnowledgeRecord`s yet, so
   this is exercised directly in `tests/knowledge/test_knowledge_record_store.py`
   rather than through a real Fact/Event pipeline.

5. **A minimal `AnalysisRun` manifest.** **Shipped.**
   [`AnalysisRun`/`StageRecord`/`StageOutcome`](../../sceneforge/runtime/analysis_run.py)
   (`ATTEMPTED`/`SKIPPED`/`FAILED`), wired as an opt-in `analysis_run`
   parameter into `Pipeline.run_detailed()` and
   `AsyncPipeline.run_detailed()`/`run_many()` — real integration, not a
   standalone type nobody produces: it taps the cache-hit/fresh-run
   distinction and retry/duration data Pipeline already computed
   internally, and adds a catch-and-reraise around
   `IncompatibleMediaError` specifically to capture the `SKIPPED` case.
   Recording never suppresses the underlying exception — it's a side
   channel, not a way to swallow a skip or a failure. `run_many()`
   shares one manifest across a whole concurrent batch. See
   `tests/runtime/test_analysis_run.py` and the integration tests in
   `tests/core/test_pipeline_resilience.py` /
   `tests/core/test_async_pipeline.py`, which exercise all four real
   outcomes end to end rather than only the type in isolation.

   One design call made during implementation, not specified verbatim
   in this ADR: `AnalysisRun.coverage()` (a dict of outcome → count) was
   added as the smallest query that makes "compute real coverage" (this
   item's own stated purpose) concrete rather than aspirational. This is
   slightly more than pure recording, which is otherwise this project's
   default posture toward new query surface — justified here because
   "coverage" is the word this ADR itself uses to describe why the item
   exists, not a speculative extension beyond it.

   **Not shipped as originally described:** `StageRecord` carries
   `provider_name`/`provider_version`, not a separate "model version" —
   no shipped provider distinguishes its own version from an underlying
   model's version yet (`WhisperTranscribeProvider`'s
   `execution_fingerprint`, not `version`, is where model configuration
   already lives, per item 2). Revisit if a real provider needs that
   distinction. There is also still no persistence for `AnalysisRun`
   itself, for the same reason as `EvidenceAnchor`/`EvidenceLink` in item
   3 — no real Application composes one multi-provider session yet.

**Explicitly deferred, not forgotten:** provider-neutral artifact contracts
(interchangeable captioners/object-detectors; the Runtime decoding-boundary
honesty gap). Normalizing an interface from a single real implementation is
the speculative abstraction this project has consistently avoided (see the
pattern behind ADR-0011, ADR-0016, ADR-0018: build the second real case,
then extract the shared shape). The Phase 1 captioning/object-detection
provider may define its own concrete output without claiming
interchangeability; normalization is revisited only once a second real
implementation of the same capability gives the abstraction two real cases
to fit, not before.

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
  "media identity + provider name + provider version" is now, as shipped,
  "content identity + provider name + provider version + execution
  fingerprint." No `Media` field carries edition identity yet — that part
  of item 2 remains deferred, see item 2 above — so there is no edition
  scope to reason about until it exists. ADR-0008's
  `ArtifactStore`/`FileArtifactStore`/`InMemoryArtifactStore` protocol and
  persistence design are unaffected and remain in force — only the key
  basis changes.
- ADR-0008's open question ("what should `Media.evolve()` mean for cache
  invalidation across multiple enrichers?", tracked as an Open RFC in
  `PROJECT_STATE.md`) is resolved in the sense that content identity no
  longer derives from `Media.id`, so `evolve()` calls that only merge
  descriptive metadata no longer affect the cache key at all (identity
  depends only on `metadata["source"]` and `media.name`). The stronger
  claim — that changed/transformed bytes reliably produce a new identity
  via `evolve()` specifically — holds by construction but has no dedicated
  regression test yet.
- Phase 1 (the captioning/object-detection provider named in
  `NEXT_TASK.md`) is unblocked: all five Phase-0 items have shipped.
- `content_key()`'s change was breaking, as accepted. Every existing
  provider call site (`Pipeline`, `AsyncPipeline`) and every test
  constructing a `content_key()` by hand were updated. Three duck-typed
  test fixtures across `tests/core/test_pipeline_resilience.py` needed to
  start subclassing the `Provider` ABC instead of hand-duplicating its
  shape, once `execution_fingerprint` became part of the structural
  contract both `Provider` protocols expose.
- The evidence-anchor/lookup work stays index-only, consistent with the
  project's standing anti-graph-database rule. The cache/evidence split
  (item 4) means a future builder *can* record an `EvidenceLink` durably
  via `KnowledgeRecordStore` so it outlives an evictable
  `FileArtifactStore` cache entry it references — but nothing enforces
  that yet, since no builder does either today. `KnowledgeRecordStore`
  is a distinct type from `EntityStore`, not a constraint layered on top
  of it, so nothing stops a future builder from writing an
  `EvidenceLink` into the wrong store; that discipline is a code-review
  concern until (if ever) a real misuse motivates enforcing it in types.
- `Pipeline.run_detailed()`/`AsyncPipeline.run_detailed()`'s public
  signatures grew a fourth optional parameter (`analysis_run`), the
  second breaking-adjacent-but-additive signature change in this ADR
  (after `execution_fingerprint` in item 2). Both are backward
  compatible — omitting the new parameter reproduces prior behavior
  exactly, verified directly (`test_pipeline_run_without_analysis_run_is_unaffected`,
  `test_async_pipeline_run_without_analysis_run_is_unaffected`) — but
  Pipeline's constructor/method surface is accumulating optional
  parameters (`capability_registry`, `enricher`, `store`, `max_retries`,
  `retry_backoff_seconds`, now `analysis_run`) across five ADRs. Worth a
  future look at whether that surface should be grouped (a
  `PipelineOptions` object or similar) once a sixth reason to grow it
  appears, rather than continuing to add positional-adjacent keyword
  parameters one ADR at a time.
- `NEXT_TASK.md` and `PROJECT_STATE.md` are updated to reflect all five
  Phase-0 items as shipped, and Phase 1 as the current objective.

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
