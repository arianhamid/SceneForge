# Project State

Live snapshot — update this when repository truth changes. See
`.ai/NEXT_TASK.md` for the active, prioritized task list.

## Current Sprint

Genesis Sprint 14: a 2026-07-22 implementation review of the comprehensive
movie-understanding research direction reproduced live identity, provenance,
and evidence-lineage defects in the current foundation (ADR-0024). Sprint 13's
objective — a real captioning or object-detection provider toward the "Facts"
rung (ADR-0021) — is deferred until ADR-0024's Phase 0 lands: trustworthy
media/execution identity, durable evidence anchors, a cache/evidence split,
and a run manifest. `Entity.provenance` now round-trips through `EntityStore`
(the first Phase-0 item, shipped); `content_key()`'s identity redesign is
decided but not yet implemented.

## Completed

- Layers 0-3 (Media, Runtime, Providers, Artifacts) are implemented and tested.
- Five real feature providers span video/audio and image domains:
  `sceneforge.contrib.ffmpeg`, `sceneforge.contrib.scenedetect`,
  `sceneforge.contrib.whisper`, `sceneforge.contrib.opencv`, and
  `sceneforge.contrib.tesseract`. `MediaHashProvider` is also available as a
  dependency-free utility provider.
- Layer 4 has three Artifact-to-Entity builders: `SceneGroupingBuilder`,
  `SceneFaceBuilder`, and `SceneTextBuilder`. `SceneSequenceBuilder` and
  `SceneMergeBuilder` implement the separate Entity-to-Entity relationship
  stage.
- `EntityStore` persistence and plain-Python querying were measured sufficient
  for targeted relationship lookup, cross-builder merging, and full-library
  aggregation (ADRs 0012, 0014, 0018, and 0019).
- `Entity.provenance`, structured knowledge validation, meaningful
  `ArtifactCategory` values, and architecture import-rule tests are shipped.
- `sceneforge.applications.SceneSummary` is the first real application. It reads
  stored scene entities and renders a Markdown scene summary.
- The runnable end-to-end example covers real frame extraction and scene
  detection, knowledge construction, relationships, optional face detection,
  cross-builder merging, and cache reuse.
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
- `CAPTION` and `OBJECT_DETECTION` remain registered capabilities without real
  implementations. OCR is real, but OCR output alone does not constitute Facts.
- `ArtifactStore` has no enumeration method equivalent to `EntityStore.keys()`;
  no real artifact-query caller has required it yet.
- `content_key()` derives from `Media.id`, a random UUID assigned per load, not
  from file content or provider configuration. Reloading the same unchanged
  file is a false cache miss; two differently configured runs of the same
  provider are a false cache hit. Decided in ADR-0024, not yet implemented.
- `Artifact`/`Entity` have no durable evidence anchor and `ArtifactStore` has
  no lookup by artifact ID, media, or time, so no application can reliably
  resolve a conclusion back to its source evidence. Decided in ADR-0024, not
  yet implemented.
- The same JSON store serves, without distinction, as an evictable
  computation cache and an implied durable evidence record. Decided in
  ADR-0024 (separate the two roles), not yet implemented.
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
  captioning/object-detection provider; provenance round-tripping shipped
  immediately, the rest is decided but not yet implemented.
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
cache invalidation across multiple enrichers?") is closed by ADR-0024 and
resolved by that ADR's Phase-0 item 2: metadata-only evolution over the same
bytes preserves content identity, changed or transformed bytes receive a new
identity, and output-affecting evolved values enter the execution fingerprint.

Cross-builder merging, cross-video querying, and runtime provider wiring are
closed decisions, not open RFCs (ADRs 0018, 0019, and 0017 respectively).

## Future Ideas

- A CLI once provider composition has a concrete user workflow.
- SQLite or graph-backed stores if measured queries outgrow current storage.
- A DNN-based face detector if real accuracy requirements justify it.
- `ArtifactStore.keys()` when a real artifact-enumeration use case appears.

## Immediate Goal

Finish ADR-0024's Phase 0: redesign `content_key()` around content identity and
an execution fingerprint while retaining edition identity for provenance/run
scope; add a minimal typed evidence-anchor/evidence-link contract with artifact
lookup by ID/media; separate the evictable computation cache from a durable,
revision-aware evidence record; add a minimal `AnalysisRun` manifest. Only then
build a real captioning or object-detection provider and the minimal builder
that turns its output into objective Fact entities. Keep Events, State,
Intentions, Narrative, and Themes deferred until the lower rungs exist.
