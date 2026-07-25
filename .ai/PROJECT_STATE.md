# Project State

Live snapshot — update this when repository truth changes. See
`.ai/NEXT_TASK.md` for the active, prioritized task list.

## Current Sprint

Genesis Sprint 14: a 2026-07-22 implementation review of the comprehensive
movie-understanding research direction reproduced live identity, provenance,
and evidence-lineage defects in the current foundation (ADR-0024). Sprint 13's
objective — a real captioning or object-detection provider toward the "Facts"
rung (ADR-0021) — was deferred until ADR-0024's Phase 0 landed: trustworthy
media/execution identity, durable evidence anchors, a cache/evidence split,
and a run manifest. All five Phase-0 items have now shipped: `Entity.provenance`
round-trips through `EntityStore`; `content_key()` derives from real content
identity plus a provider execution fingerprint instead of the random per-load
`Media.id` (edition identity itself remains an unshipped, deliberately
deferred field — see ADR-0024); a typed evidence contract (`EvidenceAnchor`,
`EvidenceLink`, `Reference`) plus `ArtifactStore` lookup by ID and by media
exist, though nothing persists an `EvidenceLink` yet since no builder produces
one; `KnowledgeRecordStore` exists as the durable, append-only, revision-aware
counterpart to `EntityStore`'s evictable cache; and `AnalysisRun` (with
`StageRecord`/`StageOutcome`) is wired live into `Pipeline`/`AsyncPipeline` as
an opt-in parameter, recording ATTEMPTED/SKIPPED/FAILED outcomes without
altering existing return/raise behavior. Phase 1 followed: `TransformersCaptionProvider`
(`Capability.CAPTION`) is real, and `FactExtractionBuilder` converts its
`CaptionArtifact` output into `Fact`-kind Entities (`EntityKind.FACT`) —
proven end to end against a real ffmpeg-generated image through a real
`Pipeline`. `TransformersObjectDetectionProvider` (`Capability.OBJECT_DETECTION`)
followed as the second real case, built specifically to test whether
`FactExtractionBuilder`'s shape generalized — the artifact count did, the
statement-synthesis logic didn't (now dispatches per artifact type), and
`Provenance.confidence` got its first real value from detection scores.
`sceneforge.applications.SceneSummary` renders both without modification. The
Facts rung of the Understanding Ladder (ADR-0021) is real, with two
independent real inputs, for the first time.

## Completed

- Layers 0-3 (Media, Runtime, Providers, Artifacts) are implemented and tested.
- `content_key()` derives from real content identity (file-bytes hash, with a
  documented name-based fallback for media with no backing file) plus a
  provider `execution_fingerprint`, not the random per-load `Media.id`
  (ADR-0024 Phase 0 item 2). `WhisperTranscribeProvider` overrides
  `execution_fingerprint` with its `transcribe_kwargs`, the concrete case
  that motivated this.
- `EvidenceAnchor`, `EvidenceLink`, and typed `Reference` (`kind`, `id`)
  exist (`sceneforge/core/evidence.py`), plus `ArtifactStore.keys()` and
  lookup by artifact ID and by media (`find_artifact_by_id()`,
  `find_artifacts_by_media()` in `sceneforge/core/storage.py`) — ADR-0024
  Phase 0 item 3.
- `KnowledgeRecordStore` (`FileKnowledgeRecordStore`,
  `InMemoryKnowledgeRecordStore` in `sceneforge/knowledge/storage.py`) is
  the durable, append-only, revision-aware counterpart to `EntityStore`'s
  evictable cache — `append()`/`retract()` only, no `put`/`delete` —
  ADR-0024 Phase 0 item 4.
- `AnalysisRun`/`StageRecord`/`StageOutcome`
  (`sceneforge/runtime/analysis_run.py`) are wired as an opt-in
  `analysis_run` parameter into `Pipeline.run_detailed()` and
  `AsyncPipeline.run_detailed()`/`run_many()`, recording
  ATTEMPTED/SKIPPED/FAILED outcomes (cache hit vs. fresh run, retries,
  duration) without altering existing return/raise behavior when
  omitted — ADR-0024 Phase 0 item 5. Phase 0 is complete.
- Seven real feature providers span video/audio and image domains:
  `sceneforge.contrib.ffmpeg`, `sceneforge.contrib.scenedetect`,
  `sceneforge.contrib.whisper`, `sceneforge.contrib.opencv`,
  `sceneforge.contrib.tesseract`, `sceneforge.contrib.transformers_caption`
  (`TransformersCaptionProvider`, `Capability.CAPTION` — the first provider
  toward the Facts rung named in ADR-0021, Phase 1 of ADR-0024's roadmap),
  and `sceneforge.contrib.transformers_object_detection`
  (`TransformersObjectDetectionProvider`, `Capability.OBJECT_DETECTION` — the
  second, built specifically to test whether `FactExtractionBuilder`'s shape
  generalized; an empty detection result is a valid outcome here, unlike an
  empty caption). Both wrap an injected `transformers` pipeline, same
  dependency-injection shape as `WhisperTranscribeProvider`; only
  `ImageMedia` accepted, not `VideoMedia`; neither verified against real
  downloaded model weights, matching Whisper's own caveat.
  `MediaHashProvider` is also available as a dependency-free utility
  provider.
- Layer 4 has four Artifact-to-Entity builders: `SceneGroupingBuilder`,
  `SceneFaceBuilder`, `SceneTextBuilder`, and `FactExtractionBuilder`
  (`CaptionArtifact`/`ObjectDetectionArtifact` → `Fact`-kind `Entity`,
  `EntityKind.FACT` — the artifact *count* generalized cleanly across both
  real cases, the *statement text* did not (dispatches per artifact type);
  `Provenance.confidence` gets its first real, non-`None` value from
  detection scores; proven end to end against a real ffmpeg-generated image
  through a real `Pipeline`,
  `tests/knowledge/test_fact_extraction_integration.py`).
  `SceneSequenceBuilder` and
  `SceneMergeBuilder` implement the separate Entity-to-Entity relationship
  stage.
- `EntityStore` persistence and plain-Python querying were measured sufficient
  for targeted relationship lookup, cross-builder merging, and full-library
  aggregation (ADRs 0012, 0014, 0018, and 0019).
- `Entity.provenance`, structured knowledge validation, meaningful
  `ArtifactCategory` values, and architecture import-rule tests are shipped.
- `sceneforge.applications.SceneSummary` is the first real application. It reads
  stored scene entities and renders a Markdown scene summary. Also renders
  `Fact`-kind Entities as their own flat "Facts" section — not correlated to
  scenes, since nothing yet maps a Fact's source image back to a specific
  scene (would need a new cross-domain correlation mechanism, deferred until
  a real need for it appears, same discipline as everything else in this
  project).
- The runnable end-to-end example covers real frame extraction and scene
  detection, knowledge construction, relationships, optional face detection
  and OCR, Facts extraction (captioning + object detection) with a
  rendered `SceneSummary`, cross-builder merging, and cache reuse
  (`--no-facts` skips the one step needing real network access). Actually
  run against a real ffmpeg-generated video in this environment, not just
  written and assumed to work — caught and fixed a real bug this way: the
  Facts step originally crashed the whole script with an unhandled
  `OSError` when `transformers` was installed but model weights weren't
  reachable, instead of degrading gracefully like every optional step
  around it.
- The Registry/Pipeline runtime-wiring RFC is closed as unnecessary (ADR-0017).
- ADRs through 0024 document the current architecture, provider decisions, and
  Python compatibility baseline.
- AI-assisted development now has repository-wide instructions, a human guide,
  reproducible quality commands, Python 3.12 CI, dependency updates, and a
  pull-request review checklist.

## Known Problems

- No dedicated Knowledge Graph (Layer 5) or Intelligence engine (Layer 6)
  exists. `Entity` + `EntityStore` + iteration have covered every measured query
  so far; add infrastructure only when a real query demonstrates a gap.
- `Pipeline` does not compose multiple providers into one ordered flow. Callers
  compose one `Pipeline` per provider in application code.
- `FileArtifactStore` and `FileEntityStore` are JSON-per-key directories. A
  different backend remains deferred until measurement justifies it.
- `WhisperTranscribeProvider` has not been verified here against downloaded real
  model weights. Its boundary logic is unit-tested with a structural fake.
- `OpenCVFaceDetectionProvider` has not been positively verified here against a
  real face photograph. Its mechanics and negative path are tested.
- `TransformersCaptionProvider` and `TransformersObjectDetectionProvider` have
  not been verified here against a real `transformers` pipeline with
  downloaded weights (this sandbox has no network access to the Hugging Face
  Hub and no `torch` installed). Both providers' boundary logic is
  unit-tested with a structural fake; the real `transformers.Pipeline` class
  shape is checked without instantiation.
- `FactExtractionBuilder` only extracts `Fact`-kind Entities from
  `CaptionArtifact`s and `ObjectDetectionArtifact`s. No deduplication of
  overlapping detections, no synthesis across caption/detection/OCR text
  describing the same frame, no confidence thresholding beyond whatever the
  provider's own `threshold` already applied. Deliberately narrow — see its
  module docstring. `source_frame_path` now flows into each Fact's metadata
  (both artifact types carry it), but no builder correlates it to a
  specific `Scene` yet.
- Fixed while writing this entry: `TransformersObjectDetectionProvider`
  declared `ObjectDetectionArtifact.source_frame_path` but never populated
  it (silently always `""`), and `CaptionArtifact` had no such field at
  all despite `FaceDetectionArtifact`/`OCRTextArtifact` already carrying
  it. Both now populate it, matching the established pattern. Also fixed:
  `sceneforge/contrib/tesseract/__init__.py`'s docstring claimed OCR was
  "the first real capability toward the 'Facts' rung," directly
  contradicting ADR-0022's own explicit title ("Still Evidence Not
  Facts") — corrected to point at the providers that actually reach
  Facts.
- `Media` has no reserved field for edition identity (the logical work and
  specific cut). Explicitly deferred by ADR-0024 rather than added
  speculatively ahead of a real consumer — revisit when Phase 4 (external
  identity/context) needs it.
- `ArtifactStore` lookup exists by artifact ID and by media
  (`find_artifact_by_id()`, `find_artifacts_by_media()`), but not by time —
  finding "everything anchored near timestamp T" still requires the caller
  to filter `iter_all_artifacts()` itself. No real query has needed it yet.
- `EvidenceAnchor`/`EvidenceLink` (ADR-0024 item 3) have no persistence
  support — nothing serializes them to/from JSON, since no builder produces
  either type yet. Add it when a real Fact/Event builder needs to store
  one, the same way `Entity.provenance` gained serialization only once it
  actually needed to survive a round trip (and initially didn't, see the
  2026-07-22 implementation review).
- `KnowledgeRecordStore` (ADR-0024 item 4) is a distinct type from
  `EntityStore`, not a constraint layered on top of it — nothing stops a
  future builder from writing durable conclusions into the evictable
  `EntityStore` cache instead. No real builder does either yet, so this
  is a code-review concern for now, not an enforced one.
- `MappingProxyType` on `Artifact`/`Entity` protects only the outer metadata
  mapping; nested lists/dicts (e.g. frame lists, face maps) remain mutable in
  place, confirmed by direct reproduction. Explicitly deferred past Phase 0
  by ADR-0024 — the cache/evidence separation above does not fix this by
  itself; revisit once a typed Fact/Event payload exists to design a frozen
  shape against.

## Architectural Decisions

See `docs/adr/`. The most recent decisions are:

- ADR-0024: Phase 0 (trustworthy media/execution identity, durable evidence
  anchors, a cache/evidence split, a run manifest) precedes the Facts-rung
  captioning/object-detection provider. All five items have shipped:
  provenance round-tripping, the content-identity/execution-fingerprint
  `content_key()` redesign, the typed evidence contract
  (`EvidenceAnchor`/`EvidenceLink` plus artifact lookup by ID/media),
  `KnowledgeRecordStore` (the durable, revision-aware counterpart to
  `EntityStore`'s cache), and `AnalysisRun` (wired live into
  `Pipeline`/`AsyncPipeline`). Phase 1 is next.
- ADR-0023: Python 3.12 is the sole supported feature release so local tooling,
  typing, and CI share one verified baseline while patch releases remain floating.
- ADR-0022: Tesseract provides real OCR and confirms frame-path correlation for
  a second cross-domain builder, while remaining at the Evidence rung.
- ADR-0021: the Understanding Ladder supplies vocabulary and explicit triggers;
  higher rungs are not built ahead of real inputs.
- ADR-0020: the stable public API surface is documented.
- ADR-0019: full-library aggregation remains fast enough with store enumeration
  and Python filtering at the measured scale.
- ADR-0018: cross-builder scene merging reuses `RelationshipBuilder`.
- ADR-0017: runtime provider Registry/Pipeline wiring is closed as unnecessary.
- ADR-0016: cross-domain builders correlate per-frame results through
  `source_frame_path` rather than a new protocol.
- ADR-0015: bundled model data does not require model injection; downloaded
  weights still follow ADR-0010's injected-model pattern.

## Open RFCs

None open. The previous entry ("what should `Media.evolve()` mean for
cache invalidation across multiple enrichers?") is closed by ADR-0024.
Content identity no longer derives from `Media.id` at all, so `evolve()`
calls that only merge descriptive metadata no longer affect the cache key —
holds by construction, since identity depends only on `metadata["source"]`
and `media.name`. The stronger claim (changed/transformed bytes reliably
produce a new identity via `evolve()` specifically) holds by the same
construction but has no dedicated regression test yet.

Cross-builder merging, cross-video querying, and runtime provider wiring are
closed decisions, not open RFCs (ADRs 0018, 0019, and 0017 respectively).

## Future Ideas

- A CLI once provider composition has a concrete user workflow.
- SQLite or graph-backed stores if measured queries outgrow current storage.
- A DNN-based face detector if real accuracy requirements justify it.
- A `PipelineOptions`-style grouping for `Pipeline`'s accumulating optional
  constructor/method parameters, if a sixth reason to grow that surface
  appears (ADR-0024's Consequences).
- Persistence for `AnalysisRun`, `EvidenceAnchor`, and `EvidenceLink` once a
  real multi-provider Application or Fact/Event builder needs to store one.
- A cross-domain correlation builder mapping `Fact` entities back to the
  `Scene` they belong to (via `source_frame_path`, matching
  `SceneFaceBuilder`/`SceneTextBuilder`'s existing pattern, ADR-0016) once
  a real report needs Facts organized by scene rather than as a flat list.

## Immediate Goal

ADR-0024's Phase 0 is complete, and Phase 1 has delivered a real Facts rung:
`TransformersCaptionProvider` is real, and `FactExtractionBuilder` converts
its `CaptionArtifact` output into `Fact`-kind Entities, proven against real
provider output via integration test — as narrow as `SceneGroupingBuilder`
was on day one, not a general Fact-extraction framework. (It traces evidence
via `Entity.provenance.source_artifact_ids`, not the ADR-0024 item-3
`EvidenceLink`/`EvidenceAnchor` types — the builder's module docstring
explains why those weren't the right fit for a whole-image caption.)
`sceneforge.applications.SceneSummary` — the project's one real
Application, whose whole purpose is proving the knowledge layer produces
something a user can actually see — now renders Facts too, closing the
loop from provider to visible output for the first time. Keep
Events, State, Intentions, Narrative, and Themes deferred until a real need
motivates their shape, the same discipline that kept `FactExtractionBuilder`
narrow rather than speculative.
