# Changelog

All notable changes to SceneForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (Sprint 11: cross-video querying, fourth confirmation)
- `tests/knowledge/test_cross_video_query_spike.py`: a synthetic
  400-movie, 15-scenes-per-movie library (23,600 entities, 1,600 real
  `FileEntityStore` keys) exercising a genuine full-library
  aggregation (rank every movie by face count, filter by threshold) —
  deliberately shaped differently from ADR-0014's targeted-lookup
  spike, to make a fourth "no new infrastructure needed" result
  actually meaningful rather than assumed. **Result: 0.391s.**
- ADR-0019 documenting the measurement and the milestone it
  represents: for the first time, Layer 5 (Knowledge Graph) has no
  measured gap across four differently-shaped real questions.
- `docs/architecture/LAYERS.md` updated with both measurements
  side by side.
- 4 new tests.

### Added (Sprint 10: cross-builder entity merging)
- `sceneforge.knowledge.scene_merge_builder.SceneMergeBuilder` —
  combines `SceneGroupingBuilder` and `SceneFaceBuilder`'s separate
  per-scene entities into one, reusing the existing `RelationshipBuilder`
  Protocol (`Entity -> Entity`) rather than inventing a new persistence
  or merge concept. Namespaces each source builder's metadata/payload
  by builder name, so a third or fourth contributing builder needs no
  special-casing and can't silently collide on a field name.
- ADR-0018 documenting the resolution — the third time in this
  project's history (after ADR-0011, ADR-0016) that checking an
  existing shape against a new need found it already sufficient.
- Real integration test
  (`tests/knowledge/test_scene_merge_integration.py`) merging actual
  `SceneGroupingBuilder` + `SceneFaceBuilder` output (itself built from
  real `ffmpeg`/`scenedetect`/`opencv` calls), confirming both builders
  independently agree on real scene boundaries.
- `examples/end_to_end/analyze_video.py` now includes the merge step,
  printing combined dialogue+face-count output per scene; re-verified
  working end-to-end against a real video.
- `docs/architecture/LAYERS.md` updated: `RelationshipBuilder` covers
  both "these entities relate" and "these entities are the same
  thing," not just scene ordering.
- 11 new tests (10 unit, 1 real integration).

### Added (Sprint 9: cross-domain Knowledge Builder + RFC closure)
- `FaceDetectionArtifact.source_frame_path` — set automatically by
  `OpenCVFaceDetectionProvider` from the decoded image's own
  `metadata["source"]`. When that image is a video frame, this equals
  `FrameExtractionArtifact.frame_path`, which is what makes cross-
  domain correlation possible without `media_id` relinking.
- `sceneforge.knowledge.scene_face_builder.SceneFaceBuilder` —
  SceneForge's first Knowledge Builder synthesizing across two
  capability domains (video/scene structure + image/face detection).
  Resolved without a new builder Protocol shape — see ADR-0016.
- Real cross-domain integration test
  (`tests/knowledge/test_scene_face_integration.py`): real ffmpeg
  frame extraction, real scenedetect scene detection, real per-frame
  OpenCV face detection, all wired through `SceneFaceBuilder` against
  a real two-scene video.
- ADR-0016 (cross-domain correlation resolution) and ADR-0017
  (Registry/Pipeline RFC formally closed as unnecessary after six
  sprints of no real caller needing it).
- `examples/end_to_end/analyze_video.py` now includes the cross-domain
  face-detection step (optional, gracefully skipped if `opencv` isn't
  installed), re-verified working end-to-end.
- 19 new tests (9 `SceneFaceBuilder` unit tests, 1 real integration
  test, plus updated `FaceDetectionArtifact` coverage).

### Added (Sprint 8: fourth real provider, image domain)
- `sceneforge.contrib.opencv`: `OpenCVFaceDetectionProvider`
  (`Capability.FACE_DETECTION`) using OpenCV's bundled Haar cascade
  classifier — no dependency injection needed, since the trained
  weights ship inside the `opencv-python` package itself, not
  downloaded separately (a real counter-example to always assuming
  ADR-0010's injection pattern; see ADR-0015).
- `OpenCVImageEnricher` — fills in real width/height for `ImageMedia`,
  closing a gap that existed since Sprint 1 (`ImageMedia` never had an
  enricher, unlike `VideoMedia`'s `FFprobeEnricher`).
- `docs/guides/ADDING_A_PROVIDER.md`'s decision table updated with the
  bundled-vs-downloaded-weights distinction found while building this.
- Honest test-coverage note carried through docs and code: no real
  face photograph available in this sandbox (no network access);
  mechanics and the negative path are genuinely tested, positive
  detection is real but unverified here.
- 9 new tests (`tests/contrib/test_opencv_integration.py`).
- `pyproject.toml`: `opencv` optional-dependency extra;
  `[[tool.mypy.overrides]]` for `cv2` (incomplete bundled stubs).

### Deliberately not done this sprint
- A second Knowledge Builder consuming `FaceDetectionArtifact` output.
  Correlating a detected-face's `media_id` (belonging to a single
  still-frame `ImageMedia`) back to the `SceneEntity` it came from is a
  real linking question, structurally similar to but not identical to
  the transcript-relinking already solved in
  `tests/knowledge/test_scene_grouping_integration.py`. Deferred to
  Sprint 9 rather than rushed — see ADR-0015's "Alternatives
  Considered".

### Added (Sprint 7: relationship querying, measured)
- `EntityStore.keys()` — a real, previously-missing enumeration
  capability. Before this, `EntityStore` could answer "is this exact
  key present" but not "what's in here at all"; the gap was found by
  attempting the spike, not anticipated.
- `iter_all_entities()` / `find_related()`
  (`sceneforge/knowledge/storage.py`) — the query primitives built on
  `keys()`: enumerate everything, filter in memory.
- `tests/knowledge/test_query_spike.py`: a synthetic 300-movie,
  20-scenes-per-movie dataset (11,700 entities, 600 real
  `FileEntityStore` keys, real disk I/O) measuring `find_related()`
  wall-clock time. **Result: 0.125s.** No index, backend change, or
  graph library added — the measurement didn't ask for one.
- ADR-0014 documenting the measurement and the conditions under which
  it should be revisited.
- `docs/architecture/LAYERS.md` updated with a "Querying entities and
  relationships" section.

### Added (Sprint 6: entity relationships)
- `EntityKind.RELATIONSHIP` and `sceneforge.knowledge.relationship_builder`:
  `RelationshipBuilder` Protocol (`relate(entities) -> list[Entity]`,
  deliberately distinct from `KnowledgeBuilder`'s `build(artifacts)`)
  and `SceneSequenceBuilder`, the first real implementation — links
  consecutive `SCENE` entities in viewing order into `RELATIONSHIP`
  entities ("scene N precedes scene N+1").
- ADR-0013 documenting the spike's two findings: relationships fit the
  existing `Entity` shape (no new base type needed), but needed a
  genuinely separate builder Protocol (input is Entities, not
  Artifacts) — a real discovery from building it, not assumed going in.
- `docs/architecture/LAYERS.md` and `DOMAIN_MODEL.md` updated to
  describe Layer 4's two builder stages
  (`Artifacts -> Entities -> Entities`) instead of the single stage
  originally documented.
- Real integration test
  (`tests/knowledge/test_relationship_integration.py`) proving the
  full two-stage chain — real `ffmpeg` + real `scenedetect` ->
  `SceneGroupingBuilder` -> `SceneSequenceBuilder` — against a real
  three-scene video, plus confirms `EntityStore` round-trips
  `RELATIONSHIP`-kind entities with zero code changes.
- `examples/end_to_end/analyze_video.py` now includes the relationship
  step, re-verified working end-to-end this session.
- 12 new tests (10 unit, 2 integration).

### Added (Sprint 5: Entity persistence)
- `sceneforge.knowledge.storage`: `EntityStore` Protocol,
  `FileEntityStore`, `InMemoryEntityStore`, `entity_build_key()`,
  `register_entity_type()` — resolving the Sprint 4 open question of
  whether `Entity` needs its own persistence shape. It does: see
  ADR-0012 for what the spike found (field names and cache-key bases
  genuinely differ between `Artifact` and `Entity`, not just
  superficially).
- `build_with_cache()` (`sceneforge/knowledge/builder.py`) —
  `Pipeline`'s cache-check/write role for Knowledge Builders, kept as
  a plain function rather than a `Pipeline`-equivalent class, since no
  Knowledge Builder has demonstrated needing retries/timeouts/
  cancellation yet.
- ADR-0012 documenting the resolution and the two alternatives tried
  and rejected (a shared `Store[T]` generic; storing Entities inside
  `ArtifactStore` directly).
- `examples/end_to_end/analyze_video.py` now caches all three layers
  (frames, scenes, entities) and verifies cache-hit *value* equality
  (not just a boolean flag) on a second run.
- 13 new tests (`tests/knowledge/test_storage.py`) covering
  round-tripping, cache-key stability/independence-from-order/
  sensitivity-to-version-and-input-set, and `build_with_cache`'s
  cache-hit/cache-miss behavior.

### Added (Sprint 4: first Knowledge Builder)
- `sceneforge.knowledge`: the framework's first Layer 4 (Knowledge
  Builders) implementation.
  - `Entity`/`EntityKind` — the Knowledge layer's immutable base type,
    mirroring `Artifact`'s discipline (`parents` traceback, frozen
    dataclass, `MappingProxyType` metadata).
  - `KnowledgeBuilder` Protocol — `name`/`version`/`build()`,
    deliberately parallel to `Provider`.
  - `SceneGroupingBuilder` — groups `FrameExtractionArtifact` and
    `TranscriptSegmentArtifact` into the `SceneCutArtifact` time
    ranges they overlap. Transcript segments spanning a cut are
    assigned to both scenes rather than arbitrarily split. See
    ADR-0011 for why the scope stops at time-overlap grouping.
  - Proven against **real** provider output (real `ffmpeg` frame
    extraction, real `scenedetect` scene detection, fake-model
    `WhisperTranscribeProvider` per ADR-0010) in
    `tests/knowledge/test_scene_grouping_integration.py` — not just
    unit tested against hand-built artifacts, though those tests
    (`tests/knowledge/test_scene_grouping_builder.py`) exist too and
    cover the grouping math (boundary conditions, cross-media
    isolation, cross-cut transcript overlap) in detail.
- ADR-0011: the first Knowledge Builder's scope decision.
- `examples/end_to_end/analyze_video.py` now includes a Knowledge
  Builder step, verified by actually running it against a real video.

### Fixed (Sprint 4)
- `examples/core/registry_basic.py` was genuinely broken — it
  referenced `ProviderRegistry`, `JoyCaptionProvider`, and
  `WhisperProvider`, none of which exist anywhere in the codebase, and
  had no imports. It would not run. Replaced with real, working code
  demonstrating `Registry.by_capability()` against two real providers.
- `CONTRIBUTING.md` pointed at `.ai/START_HERE.md`, which doesn't
  exist. Replaced with links to docs that do.
- `docs/architecture/DOMAIN_MODEL.md`'s "Pipeline" section described
  multi-provider composition as implemented; it isn't. Now says so
  explicitly.

### Added (Sprint 3: second and third real providers)
- `sceneforge.contrib.scenedetect`: `PySceneDetectProvider`
  (`Capability.DETECT_SCENES`) — real content-aware cut detection via
  the `scenedetect` library, no model weights or network required.
  Integration tested against real generated videos including a
  `min_scene_len` tuning test that caught and demonstrated a real
  behavior (default `min_scene_len` merges cuts shorter than ~1.5s).
- `sceneforge.contrib.whisper`: `WhisperTranscribeProvider`
  (`Capability.TRANSCRIBE`) — real `faster-whisper` integration, with
  the model injected via `WhisperModelProtocol` rather than
  constructed internally, so the provider is fully unit-testable
  without network access, a GPU, or downloaded weights (see
  ADR-0010). Also the first real showcase of `SyncProviderAdapter`
  actually being used for its intended purpose (concurrent batches
  under `AsyncPipeline`).
- ADR-0010: model-backed providers take their model as a constructor
  argument, typed against a minimal structural Protocol.
- `docs/guides/ADDING_A_PROVIDER.md`: step-by-step checklist for
  adding a new provider, using all three real providers as worked
  examples.
- `examples/end_to_end/analyze_video.py` (renamed from
  `video_to_frames.py`): now runs both real video providers
  (frame extraction + scene detection) against a real file, verified
  end-to-end including cache-hit behavior on a second run.
- `pyproject.toml`: `scenedetect` and `whisper` optional-dependency
  extras.
- `[[tool.mypy.overrides]]` for `scenedetect` (no bundled type stubs).

### Added (Sprint 2: architectural resilience)
- `Media.evolve()`: sanctioned immutable path for turning placeholder
  metadata (from cheap loaders) into authoritative metadata, without
  ever mutating a `Media` instance in place
- `MediaEnricher` protocol (`sceneforge/core/enrichment.py`) and
  `ChainedEnricher`, plus `Pipeline(..., enricher=...)` integration
- `CapabilityRegistry` as an injectable object, replacing the old
  module-level global `_CAPABILITY_MEDIA_MAP` (see ADR-0007)
- `Pipeline.run_detailed()` / `PipelineResult`: real timing, retry
  count, cache status, and the (possibly enriched) `Media` actually
  processed; `Pipeline` now threads `ProcessingContext` through a run
  and wraps provider exceptions in `ProviderExecutionError` instead of
  letting them escape unbranded (see ADR-0003 update)
- `ArtifactStore` protocol, `FileArtifactStore`, `InMemoryArtifactStore`,
  and `content_key()` — content-addressable persistence making
  "analyze once, reuse forever" literally true (see ADR-0008)
- `AsyncProvider`, `SyncProviderAdapter`, and `AsyncPipeline` (timeout,
  retry, bounded concurrency via `run_many()`, partial-failure
  isolation via `BatchResult`) for I/O- and GPU-bound real providers
  (see ADR-0009)
- Entry-point based plugin discovery:
  `PluginRegistry.discover()` / `discover_plugins()`, using
  `importlib.metadata.entry_points(group="sceneforge.plugins")`
- `sceneforge.contrib.ffmpeg`: the framework's first real (non-stub)
  integration — `FFprobeEnricher` and `FFmpegFrameExtractionProvider`,
  integration tested against a real ffmpeg-generated synthetic video
- ADR-0006 through ADR-0009 recording the above decisions
- `docs/philosophy/VISION.md`, `docs/NAMING_CONVENTIONS.md`,
  `docs/STYLE_GUIDE.md` (previously empty files)
- `FRAME_EXTRACTION` capability to `Capability` enum
- `InvalidNameError` and `InvalidMetadataError` framework exceptions
- CI workflow with Ruff, mypy, and coverage checks
- Added tests for naming validation, metadata validation, and edge cases
- Added comprehensive test coverage for registry and plugin lifecycle

### Changed
- `provider_protocol.Provider` now declares the full structural
  contract (`name`, `version`, `capabilities`, `run`), not just `run()`
  — a `run()`-only class no longer satisfies `isinstance(x, Provider)`
  (see ADR-0006; this was a real, previously-unnoticed contract gap)
- Replaced wildcard imports in package `__init__.py` with explicit imports
- Updated `naming.py` and `validation.py` to use framework-specific exceptions
- Updated Python version requirement from 3.10 to 3.11 (for StrEnum support)
- Updated mypy configuration to target Python 3.11

### Removed
- Removed unused `base_provider.py` file
- Removed `register_capability_media()` / `register_default_capabilities()`
  module-level functions (superseded by `CapabilityRegistry`, ADR-0007)
- Consolidated `docs/philosophy/MANIFESTO.md`, `NORTH_STAR.md`,
  `CORE_PRINCIPLES.md`, and `TEN_COMMANDMENTS.md` (four overlapping
  restatements of the same ideas) into `docs/philosophy/VISION.md`

### Fixed
- Fixed Ruff linting error with `Mapping` import in `artifact.py`
- Fixed mypy type errors with generic type parameters
- `docs/specifications/ARTIFACT_SPEC.md`'s "Required Fields" list
  named fields (`source`, `timestamp_start`, `timestamp_end`) that
  never existed on the real `Artifact` dataclass — corrected to match
  `sceneforge/core/artifact.py` exactly
- `docs/specifications/MEDIA_SPEC.md` claimed placeholder metadata was
  "delegated to Providers" — no such mechanism ever existed; corrected
  to describe the actual `MediaEnricher` mechanism added this pass
- `.ai/NEXT_TASK.md`'s "coding order" referenced `sceneforge/ir/` and
  `sceneforge/capabilities/`, paths that never existed in the real
  repo layout — corrected

## [0.1.0] - 2024-01-01

### Added
- Initial release of SceneForge framework
- Core artifact system with immutable dataclasses
- Provider abstraction with capability system
- Pipeline execution engine
- Plugin registry for extensibility
- Identity provider for testing
- Comprehensive test suite