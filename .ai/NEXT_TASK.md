# Next Task

## Genesis Sprint 14

### Current Objective

Sprint 12 delivered the first real Application (`SceneSummary`),
an architecture-enforcing test suite, a utility provider
(`MediaHashProvider`), and knowledge-entity validation — all real,
tested, and verified. ADR-0021 then reconciled a much larger vision
(the "Understanding Ladder": Evidence → Facts → Entities → Events →
State → Relationships → Intentions → Narrative → Themes) against this
project's established discipline: adopt what's already real as
vocabulary, document the rest as direction with explicit trigger
conditions, build nothing ahead of a real data source. Sprint 13's
objective is the first rung of that ladder that isn't built yet:
**Facts**, which requires a provider that produces something above
raw detection.

Sprint 13 has since delivered real Tesseract OCR and `SceneTextBuilder`
(ADR-0022). That work expands and organizes Evidence but does not interpret it
into objective Facts, so the captioning/object-detection objective below
remains the eventual target — but a 2026-07-22 implementation review of the
comprehensive movie-understanding research direction reproduced live defects
in the identity and evidence foundation that objective would be built on
(random `Media.id` in `content_key()`, unserializable `Provenance`, no way to
resolve a conclusion back to its evidence, nested "immutable" payloads that
mutate in place). ADR-0024 inserts a Phase 0 ahead of the captioning/
object-detection provider to fix that foundation first. `Entity.provenance`
now round-trips through `EntityStore`, `content_key()` now derives from
real content identity plus a provider execution fingerprint instead of the
random per-load `Media.id`, a typed evidence contract
(`EvidenceAnchor`/`EvidenceLink`) plus `ArtifactStore` lookup by ID and by
media now exist, `KnowledgeRecordStore` now exists as the durable,
append-only, revision-aware counterpart to `EntityStore`'s evictable
cache, and `AnalysisRun` is now wired live into `Pipeline`/`AsyncPipeline`
as an opt-in parameter. Phase 0 is complete. Phase 1 has started:
`TransformersCaptionProvider` (`Capability.CAPTION`) is real, wrapping an
injected `transformers` `image-text-to-text` pipeline the same way
`WhisperTranscribeProvider` wraps faster-whisper. `FactExtractionBuilder`
now converts its `CaptionArtifact` output into `Fact`-kind Entities
(`EntityKind.FACT`), proven end to end against a real ffmpeg-generated
image through a real `Pipeline`. The Facts rung of the Understanding
Ladder is real, narrowly, for the first time.

---

## Completed (Sprints 1-14)

- Layers 0-3: six real feature providers across video/audio and image domains
  (`ffmpeg`, `scenedetect`, `whisper`, `opencv`, `tesseract`,
  `transformers_caption`), plus the dependency-free `MediaHashProvider`
  utility.
- Layer 4: four Artifact-to-Entity Knowledge Builders
  (`SceneGroupingBuilder`, `SceneFaceBuilder`, `SceneTextBuilder`,
  `FactExtractionBuilder`) and two
  Entity-to-Entity Relationship Builders (`SceneSequenceBuilder`,
  `SceneMergeBuilder`). `EntityStore` persistence/querying has been measured
  four times at real scale (ADR-0012, 0014, 0018, 0019).
- `sceneforge/knowledge/validation.py` — structural validation for
  entities (orphan scenes, self-references, duplicate indices,
  timeline checks), returning typed `ValidationIssue`s.
- `Entity.provenance` (`Provenance`: builder, source_artifact_ids,
  confidence) — real, shipped, independently converging with the
  world-model vision document's "every fact remembers why the system
  believes it."
- **First real Application**: `sceneforge.applications.scene_summary.SceneSummary`
  — reads real scene entities from an `EntityStore`, renders a
  Markdown summary. Proves `docs/philosophy/VISION.md`'s own success
  definition for the first time.
- **Architecture test suite** (`tests/architecture/test_import_rules.py`)
  — AST-based enforcement of the real dependency graph (core/knowledge/
  media/runtime/contrib boundaries), including a `TestKnownDependencies`
  class that positively asserts the real, deliberate ADR-backed
  dependencies (e.g. `core.pipeline` → `runtime.ProcessingContext`,
  `knowledge` → specific `contrib` artifact types) are never
  accidentally flagged.
- ADR-0020 (stable API surface), ADR-0021 (world-model vocabulary
  reconciliation — the Understanding Ladder now documented in
  `docs/architecture/DOMAIN_MODEL.md`, each rung marked real or
  blocked-on-what).

---

## Immediate Tasks (ADR-0024 Phase 0, in order)

1. **Provenance round-trips through `EntityStore`.** Done —
   `sceneforge/knowledge/storage.py` now serializes/deserializes
   `Provenance`; see `tests/knowledge/test_storage.py`.
2. **Redesign `content_key()`'s identity basis.** Done —
   `sceneforge/core/storage.py`'s `content_key()` now derives from
   `media_content_identity()` (real file-bytes hash, documented
   name-based fallback for media with no backing file) plus
   `Provider.execution_fingerprint` (new property, default `""`,
   overridden by `WhisperTranscribeProvider` with a hash of its
   `transcribe_kwargs` — the concrete case that motivated this). Both
   `Pipeline` and `AsyncPipeline` updated; both structural `Provider`
   protocols (`core/provider_protocol.py`, `core/async_provider.py`)
   and the `Provider` ABC gained the property; see
   `tests/core/test_storage.py`. **Not done**: no reserved edition-identity
   field exists on `Media` — deferred per ADR-0024 rather than added
   ahead of a real (Phase 4) consumer. The execution fingerprint is a
   single opaque string, not yet a structured descriptor with separate
   model-ID/prompt-version/tool-version fields — defer that structure
   until a second provider needs to distinguish those dimensions
   independently.
3. **A minimal typed evidence contract.** Done —
   `sceneforge/core/evidence.py` defines `EvidenceAnchor`, `EvidenceLink`,
   and typed `Reference` (`kind`, `id` — `artifact`/`entity`/
   `external_claim`/`revision`); `EvidenceRelation` has only `supports`/
   `derived_from`, no speculative extras. `ArtifactStore` gained `keys()`
   (mirroring `EntityStore.keys()`, ADR-0014) plus `find_artifact_by_id()`
   and `find_artifacts_by_media()` in `sceneforge/core/storage.py`. No
   graph database — naive iteration over `ArtifactStore.keys()`. See
   `tests/core/test_evidence.py`, `tests/core/test_storage.py`.
   **Not done**: no persistence for `EvidenceAnchor`/`EvidenceLink` —
   deferred until a real Fact/Event builder needs to store one, not added
   speculatively (the same lesson `Provenance` taught in item 1).
4. **Separate the cache role from the evidence role.** Done —
   `sceneforge/knowledge/storage.py` adds `KnowledgeRecordStore`
   (`FileKnowledgeRecordStore`, `InMemoryKnowledgeRecordStore`): a
   distinct, durable, append-only, revision-aware store alongside the
   unchanged `EntityStore` cache. `append()` always creates a new
   numbered revision and never overwrites or deletes one; `retract()`
   records withdrawal as a new dated revision rather than erasing the
   original. `FileArtifactStore`/`FileEntityStore` are untouched — same
   evictable cache role as before. Initially the same JSON-per-file
   format as `FileEntityStore`, as anticipated — only the *role*
   changed, not the storage technology. See
   `tests/knowledge/test_knowledge_record_store.py`. **Not done**: no
   type-level enforcement stops a future builder from writing durable
   conclusions into `EntityStore` instead of `KnowledgeRecordStore` — a
   code-review concern until a real misuse motivates enforcing it.
5. **A minimal `AnalysisRun` manifest.** Done —
   `sceneforge/runtime/analysis_run.py` defines `AnalysisRun`,
   `StageRecord`, and `StageOutcome` (`ATTEMPTED`/`SKIPPED`/`FAILED`),
   wired as an opt-in `analysis_run` parameter into
   `Pipeline.run_detailed()` and
   `AsyncPipeline.run_detailed()`/`run_many()`. Real integration, not a
   standalone type: it taps the cache-hit/fresh-run distinction and
   retry/duration data Pipeline already computed, and catches-then-
   reraises `IncompatibleMediaError` to capture the SKIPPED case.
   `run_many()` shares one manifest across a whole concurrent batch.
   Omitting `analysis_run` reproduces prior behavior exactly (verified
   directly). See `tests/runtime/test_analysis_run.py` and the
   integration tests in `tests/core/test_pipeline_resilience.py` /
   `tests/core/test_async_pipeline.py`. **Not done**: no persistence for
   `AnalysisRun` itself (same reasoning as item 3's deferred
   persistence — no real multi-provider session exists yet to need it);
   `StageRecord` has no separate "model version" field distinct from
   `provider_version` (no shipped provider needs that distinction yet).

Phase 0 is complete. Start Phase 1:

6. **A real `CAPTION` or `OBJECT_DETECTION` provider.** Done —
   `sceneforge/contrib/transformers_caption/` (`TransformersCaptionProvider`,
   `CaptionArtifact`), the actual blocker named explicitly in ADR-0021
   for the Facts rung. Wraps an injected `transformers`
   `image-text-to-text` pipeline (ADR-0010's dependency-injection
   pattern, since real weights need network access this environment
   doesn't have — the same shape as `WhisperTranscribeProvider`, not
   OpenCV's bundled-weights shape; see
   `docs/guides/ADDING_A_PROVIDER.md` step 2's decision table). The
   `ImageTextToTextPipelineProtocol` was modeled on
   `transformers==5.14.1`'s actual installed source
   (`transformers/pipelines/image_text_to_text.py`), not guessed. Only
   `ImageMedia` accepted — `Capability.CAPTION` is registered for
   `VideoMedia` too, but captioning a whole video needs a
   frame-selection decision this provider deliberately doesn't make;
   see the module docstring. See
   `tests/contrib/test_transformers_caption.py` (14 tests, matching
   every category in `ADDING_A_PROVIDER.md` step 7, including the
   real-class-shape contract test). **Not verified**: against real
   downloaded model weights (no Hugging Face Hub access, no `torch`
   installed here) — same caveat `WhisperTranscribeProvider` already
   carries.
7. **A minimal `FactExtractionBuilder`.** Done —
   `sceneforge/knowledge/fact_extraction_builder.py` turns each
   `CaptionArtifact` into one `Fact`-kind Entity (`EntityKind.FACT`,
   new). As narrow as `SceneGroupingBuilder` was on day one: one real
   transformation, no deduplication across multiple captions of the
   same frame, no synthesis with OCR text, no contradiction handling.
   Proven against real provider output via integration test
   (`tests/knowledge/test_fact_extraction_integration.py`: real
   ffmpeg-generated image, real `Pipeline`, real content-identity
   caching, fake captioning model injected). **Traces evidence via
   `Entity.provenance.source_artifact_ids`, not the item-3 evidence
   contract** (`EvidenceLink`/`EvidenceAnchor`) — a caption describes a
   whole image with no natural sub-image interval for `EvidenceAnchor`,
   and `provenance.source_artifact_ids` (real since item 1) already
   gives full traceability via `find_artifact_by_id()`; see the
   builder's module docstring for the full reasoning. `EvidenceLink`
   remains unused, reserved for typed relationships *between* Entities
   that don't exist yet.
8. Do **not** start Events, State, Relationships-beyond-scenes,
   Intentions, Narrative, or Themes yet. Facts now exists (narrowly),
   so they're no longer *blocked* the way they were — but "unblocked"
   is not "needed yet." Building any of them before a real Event/State/
   etc. need appears would repeat the exact mistake this project has
   now avoided nine separate times, just one rung higher.

Provider-neutral artifact contracts and the Runtime decoding-boundary gap are
explicitly deferred past Phase 0. The first provider for a new capability may
define a concrete output; normalize it only when a second implementation of the
same capability provides another real case to design against.

---

## Coding Order

Phase 0 (ADR-0024) — items 2–5 of the Immediate Tasks above, numbered here
by coding order rather than by that list's numbering:

1. Done — content identity + execution fingerprint in
   `sceneforge/core/storage.py` (`content_key()`, `media_content_identity()`),
   `sceneforge/core/provider.py`/`provider_protocol.py`/`async_provider.py`
   (`execution_fingerprint`), and the sync/async Pipeline cache call sites.
   No edition-identity field — deferred, see Immediate Tasks item 2 above.
2. Done — typed evidence contract in `sceneforge/core/evidence.py`
   (`EvidenceAnchor`, `EvidenceLink`, `Reference` with `(kind, id)`
   endpoints) plus `ArtifactStore.keys()`, `find_artifact_by_id()`, and
   `find_artifacts_by_media()`. No persistence for the new types yet —
   deferred, see Immediate Tasks item 3 above.
3. Done — `KnowledgeRecordStore` in `sceneforge/knowledge/storage.py`
   (`FileKnowledgeRecordStore`, `InMemoryKnowledgeRecordStore`),
   distinct from the unchanged `EntityStore` cache. See
   `tests/knowledge/test_knowledge_record_store.py`.
4. Done — `AnalysisRun`/`StageRecord`/`StageOutcome` in
   `sceneforge/runtime/analysis_run.py`, wired into
   `Pipeline`/`AsyncPipeline` as an opt-in `analysis_run` parameter.
   See `tests/runtime/test_analysis_run.py`,
   `tests/core/test_pipeline_resilience.py`,
   `tests/core/test_async_pipeline.py`.

Phase 0 (ADR-0024) is complete. Start Phase 1:

5. Done — `sceneforge/contrib/transformers_caption/` (`CaptionArtifact`,
   `TransformersCaptionProvider`). See
   `tests/contrib/test_transformers_caption.py`.
6. Done — `sceneforge/knowledge/fact_extraction_builder.py`
   (`FactExtractionBuilder`, new `EntityKind.FACT`). See
   `tests/knowledge/test_fact_extraction_builder.py`.
7. Done — real integration test combining (5) and (6) against a real
   ffmpeg-generated image, the same discipline as every prior
   Knowledge Builder. See
   `tests/knowledge/test_fact_extraction_integration.py`.

The Facts rung of the Understanding Ladder (ADR-0021) is real, with two
independent real providers (`CAPTION`, `OBJECT_DETECTION`) confirming the
`FactExtractionBuilder` shape generalizes for artifact count (not for
statement synthesis, which is per-artifact-type by design). Next: decide,
based on a real need rather than the roadmap alone, whether Events, a
Fact-to-scene correlation builder (see `PROJECT_STATE.md`'s Future Ideas),
or something else is the right next step — see Immediate Tasks item 8
above.

---

## Success Criteria

Phase 0 (ADR-0024):

- [x] `content_key()` derives from content identity plus an execution
      fingerprint, not a random `Media.id`; reloading the same
      unchanged file is a cache hit, two differently configured
      provider runs are not a false hit. Verified directly, see
      `tests/core/test_storage.py`.
- [x] `Provenance` round-trips through `EntityStore` — done, see
      `tests/knowledge/test_storage.py`.
- [x] A typed `EvidenceAnchor`/`EvidenceLink` contract exists with
      artifact lookup by ID and by media — done, see
      `tests/core/test_evidence.py`, `tests/core/test_storage.py`. An
      application can resolve a stored `Reference` back to the source
      `Artifact`; nothing yet persists an `EvidenceLink` itself, since
      no builder produces one.
- [x] The evictable computation cache and durable evidence/knowledge
      record are distinct concepts, even if backed by the same file
      format initially — done, see
      `tests/knowledge/test_knowledge_record_store.py`. Type-level
      enforcement that a builder uses the right one is not done.
- [x] A minimal `AnalysisRun` manifest records provider/model/config
      versions and per-stage attempted/skipped/failed/cache-hit status —
      done, see `tests/runtime/test_analysis_run.py` and the
      integration tests in `tests/core/test_pipeline_resilience.py` /
      `tests/core/test_async_pipeline.py`.

Phase 1, once Phase 0 above is real:

- [x] A real captioning or object-detection provider exists, with
      tests matching `docs/guides/ADDING_A_PROVIDER.md`'s checklist —
      done, see `sceneforge/contrib/transformers_caption/` and
      `tests/contrib/test_transformers_caption.py`.
- [x] A first real `Fact`-producing Knowledge Builder exists, proven
      against that provider's real output via integration test — done,
      see `sceneforge/knowledge/fact_extraction_builder.py` and
      `tests/knowledge/test_fact_extraction_integration.py`. Traces
      evidence via `Entity.provenance.source_artifact_ids`, not the
      item-3 `EvidenceLink`/`EvidenceAnchor` contract (see the
      builder's docstring for why). Its payload is a plain string
      (immutable by construction, no nested mutable structure), so the
      known nested-metadata-mutability defect does not apply to the
      payload itself — `metadata` still uses the same loosely-typed
      `dict[str, Any]` every other Entity does, unresolved.
- [x] `docs/architecture/DOMAIN_MODEL.md`'s Understanding Ladder entry
      for "Facts" is updated from "Not built" to real, with the same
      honesty about what's still blocked above it — done. The Events
      entry was also corrected: it no longer claims to be "blocked on
      Facts existing first," since Facts now exists.
