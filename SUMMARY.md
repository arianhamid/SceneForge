# SceneForge Architecture Review Summary

This file tracks completed review passes. See `ARCHITECT_REVIEW.md`
for the narrative version of the most recent pass; this is the
checklist form.

## Pass 11 (Genesis Sprint 11): Cross-video querying, fourth confirmation

### Added
1. **A deliberately different question**: not another cross-builder or
   cross-domain correlation (already asked three ways), but full
   cross-video aggregation — rank every movie in a 400-movie library
   by detected face count, with no shortcut available. Result:
   **0.391s** over 23,600 entities, 1,600 store keys. See ADR-0019.
2. **Milestone**: four consecutive real measurements (ADR-0012, 0014,
   0018, 0019), each shaped differently, have all found the existing
   `Entity`/`EntityStore` design sufficient. For the first time, Layer
   5 has no obviously overdue gap — not proof it never will, but
   enough evidence to stop spiking the same question and pivot.

### Verification

- **308 tests passing** (up from 304 — 4 new).
- **`mypy --strict`**: no errors across 73 source files.
- **`ruff check`**: all checks pass, repo-wide.

### Why this pass changes the plan

Per `docs/philosophy/VISION.md`'s own success definition — someone
runs a real movie through SceneForge once, then builds real things
from that analysis — four rounds of "the infrastructure holds" without
ever having built one of those "real things" would start to miss the
actual point. Sprint 12 pivots to the first real Application.

## Pass 10 (Genesis Sprint 10): Cross-builder merging, no new concept needed

### Added
1. **`SceneMergeBuilder`** — combines `SceneGroupingBuilder` and
   `SceneFaceBuilder`'s output for the same scene into one entity.
   Built as a `RelationshipBuilder` (the same Protocol
   `SceneSequenceBuilder` already used for a *different* relationship
   type) rather than inventing anything new. See ADR-0018.
2. **Third confirmation of a pattern**: checking whether
   `KnowledgeBuilder`/`RelationshipBuilder` already cover a new need,
   before assuming a new Protocol or persistence concept is required,
   has now worked three times running (ADR-0011's builder scope,
   ADR-0016's cross-domain correlation, this one). Sprint 11 tests
   whether that's a reliable default or coincidence, against a
   genuinely different kind of need (cross-video, not cross-builder).
3. **Real proof**: merged real `SceneGroupingBuilder` + `SceneFaceBuilder`
   output (both built from real `ffmpeg`/`scenedetect`/`opencv` calls),
   confirming the two independently-built entities agree exactly on
   real scene boundaries — evidence the `(media_id, scene_index)`
   correlation key is trustworthy in practice, not just in theory.
4. `examples/end_to_end/analyze_video.py` extended with the merge
   step and re-run against a real video.

### Verification

- **304 tests passing** (up from 293 — 11 new: 10 unit, 1 real
  integration).
- **`mypy --strict`**: no errors across 73 source files.
- **`ruff check`**: all checks pass, repo-wide.

## Pass 9 (Genesis Sprint 9): Cross-domain Knowledge Builder, RFC closed

### Added
1. **`SceneFaceBuilder`** — the second real Knowledge Builder, and the
   first synthesizing across two capability domains. The anticipated
   need for a third builder Protocol shape (taking both Entities and
   Artifacts) didn't materialize once `FaceDetectionArtifact` carried
   forward `source_frame_path` — correlation by file-path equality
   sufficed within the existing `KnowledgeBuilder` shape. See ADR-0016.
2. **Real end-to-end proof**: real ffmpeg frames, real scenedetect
   cuts, real per-frame OpenCV face detection, correctly attributed to
   scenes with zero manual relinking of `media_id` — the correlating
   field was already there once the provider was taught to carry it.
3. **The Registry/Pipeline RFC, closed** (ADR-0017): six sprints of
   deferral ended with an explicit decision — no real caller ever
   needed it, so it's not built, and that's recorded as a decision,
   not a silent drop.
4. `examples/end_to_end/analyze_video.py` extended with the
   cross-domain step (gracefully optional), re-run and verified.

### Verification

- **293 tests passing** (up from 283 — 19 new: 9 unit, 1 real
  integration, plus supporting coverage).
- **`mypy --strict`**: no errors across 72 source files.
- **`ruff check`**: all checks pass, repo-wide.
- End-to-end example re-run this session against a real two-scene
  video; cross-domain face-detection output correctly attributed
  per scene.

## Pass 8 (Genesis Sprint 8): Fourth real provider, image domain

### Added
1. **`sceneforge.contrib.opencv`** — `OpenCVFaceDetectionProvider`
   (real Haar cascade face detection, bundled weights, no injection)
   and `OpenCVImageEnricher` (closes a Sprint-1-era gap: `ImageMedia`
   never had a real enricher). See ADR-0015.
2. **A genuine counter-example to ADR-0010**: not every model-backed
   provider needs dependency injection — only the ones whose weights
   aren't bundled with the library. Found by checking, not assumed.
   `docs/guides/ADDING_A_PROVIDER.md`'s decision table updated.
3. **Deliberately incomplete, on purpose**: the second Knowledge
   Builder this provider was meant to unblock is not built yet. The
   media_id-linking question (a detected face's `media_id` belongs to
   a derived still-frame image, not the source video) deserves its own
   spike, the same way every other Knowledge-layer question in this
   project got one — not a rushed bolt-on. Deferred to Sprint 9 with
   the reasoning documented in ADR-0015 rather than silently dropped.

### Verification

- **283 tests passing** (up from 274 — 9 new, all real: solid-color
  negative-detection proof, real image decoding, real error paths).
- **`mypy --strict`**: no errors across 71 source files (one new
  override for `cv2`'s incomplete stubs, plus one targeted inline
  ignore for `cv2.data`).
- **`ruff check`**: all checks pass, repo-wide.

## Pass 7 (Genesis Sprint 7): Relationship querying, measured not assumed

### Added
1. **`EntityStore.keys()`** — found missing by attempting the actual
   task, not by review. Every other `EntityStore` method requires
   knowing the key already; there was no way to ask "what's in here."
2. **`iter_all_entities()` / `find_related()`** — the query layer built
   on `keys()`.
3. **A real-scale measurement, not a guess**: 300 synthetic movies × 20
   scenes = 11,700 entities across 600 real `FileEntityStore` keys
   (actual disk I/O). `find_related()` for a scene buried in the
   middle of the dataset: **0.125 seconds.** Conclusion: no index, no
   backend change, no graph library — the evidence didn't call for one.
4. ADR-0014, and a `docs/architecture/LAYERS.md` update describing how
   querying actually works today.

### Verification

- **274 tests passing** (up from 270 — 4 new, including the scale
  spike itself, which prints its own timing for future reference).
- **`mypy --strict`**: no errors across 67 source files.
- **`ruff check`**: all checks pass, repo-wide.

### Why this pass matters beyond the number

Every open architectural question this project set out to answer
before committing to a Knowledge Graph backend is now answered with
either a working implementation or a measurement — not a design
document. Sprint 8 is the first sprint since Sprint 3 with no
foundational Knowledge-layer question left open; it can honestly pivot
to capability breadth (a fourth real provider) instead of another
spike.

## Pass 6 (Genesis Sprint 6): Entity relationships, spiked

### Added
1. **`RelationshipBuilder` Protocol + `SceneSequenceBuilder`** — the
   Sprint 6 spike answered "can relationships be represented with the
   existing `Entity` shape?" (yes) and, as a byproduct of actually
   building it rather than designing it on paper, surfaced that the
   *builder* needs a separate Protocol from `KnowledgeBuilder` (input
   is Entities, not Artifacts). See ADR-0013.
2. **Real two-stage integration test**
   (`tests/knowledge/test_relationship_integration.py`): real `ffmpeg`
   + real `scenedetect` output through `SceneGroupingBuilder`, then
   through `SceneSequenceBuilder`, against a real three-scene video —
   confirms 3 scenes correctly detected and correctly sequenced
   (0→1, 1→2), and that `EntityStore` (ADR-0012) persists
   `RELATIONSHIP`-kind entities with zero code changes, a real second
   use validating that design.
3. `docs/architecture/LAYERS.md` and `DOMAIN_MODEL.md` corrected to
   describe Layer 4's actual two-stage shape.
4. `examples/end_to_end/analyze_video.py` extended and re-run; now
   prints "scene 0 precedes scene 1" from real detected scene data.

### Verification

- **270 tests passing** (up from 258 — 12 new: 10 unit tests for
  `SceneSequenceBuilder`'s sequencing logic, 2 real integration tests).
- **`mypy --strict`**: no errors across 67 source files.
- **`ruff check`**: all checks pass, repo-wide.
- End-to-end example re-run this session against a real generated
  video; relationship output verified correct.

## Pass 5 (Genesis Sprint 5): Entity persistence, resolved by spike

### Added
1. **`EntityStore`** (`sceneforge/knowledge/storage.py`) — resolved
   the top open RFC from Sprint 4 by actually building both candidate
   designs (a shared generic with `ArtifactStore`; a separate type)
   and comparing them, rather than picking one on paper. The separate
   type won: `Artifact.provider`/`Entity.builder` are different
   vocabulary for a reason, and `content_key()`'s single-media basis
   doesn't fit `SceneGroupingBuilder`'s actual batching behavior
   (many media objects grouped in one call). See ADR-0012.
2. **`build_with_cache()`** — deliberately a function, not a
   `Pipeline`-shaped class, since nothing has shown Knowledge Builders
   need retries/timeouts/cancellation yet. Promotable later if that
   changes; not built ahead of evidence.
3. **`examples/end_to_end/analyze_video.py`** now demonstrates caching
   at all three layers and checks that a second run's entities are
   value-equal to the first (not just that a flag says "cached") —
   verified by actually running it.

### Verification

- **258 tests passing** (up from 245 — 13 new, all in
  `tests/knowledge/test_storage.py`).
- **`mypy --strict`**: no errors across 66 source files.
- **`ruff check`**: all checks pass, repo-wide.
- End-to-end example re-run this session, output confirms
  `entities match=True` on the second (cached) run.

## Pass 4 (Genesis Sprint 4): First Knowledge Builder

### Added
1. **`sceneforge.knowledge`** — `Entity`/`EntityKind`, the
   `KnowledgeBuilder` Protocol, and `SceneGroupingBuilder`: the
   framework's first Layer 4 implementation, deliberately scoped to
   time-overlap grouping only (ADR-0011) rather than attempting
   character/location/dialogue understanding before the basic
   `Artifact -> Entity` contract was proven.
2. **Real, not just unit-tested, proof**:
   `tests/knowledge/test_scene_grouping_integration.py` runs real
   `ffmpeg` frame extraction and real `scenedetect` scene detection
   through actual `Pipeline` instances, plus a fake-model
   `WhisperTranscribeProvider`, and feeds the results into
   `SceneGroupingBuilder` — confirming the Knowledge layer's design
   holds up against genuinely produced artifacts, not hand-built ones.
   17 additional unit tests cover the grouping math directly (scene
   boundary edge cases, cross-media isolation, transcript segments
   spanning a cut).
3. **`examples/end_to_end/analyze_video.py`** now includes the
   Knowledge Builder step and was re-verified end-to-end against a
   real video.
4. **Fixed a genuinely broken example**:
   `examples/core/registry_basic.py` referenced three classes that
   don't exist anywhere in the codebase and had no imports — it could
   not have ever run. Replaced with real, working code.
5. Fixed a dangling `.ai/START_HERE.md` reference in `CONTRIBUTING.md`
   (the file doesn't exist) and a `DOMAIN_MODEL.md` section describing
   unimplemented Pipeline composition as if it were current behavior.

### Verification

- **245 tests passing** (up from 227 — 18 new: 6 for `Entity`, 11 for
  `SceneGroupingBuilder`'s grouping logic, 1 real integration test
  combining three real providers' output).
- **`mypy --strict`**: no errors across 65 source files.
- **`ruff check`**: all checks pass, repo-wide including `examples/`.
- The end-to-end example, including its new Knowledge Builder step,
  was actually executed against a real generated video during this
  pass.

## Pass 3 (Genesis Sprint 3): Second and third real providers

### Added
1. **`sceneforge.contrib.scenedetect`** — `PySceneDetectProvider`
   (`Capability.DETECT_SCENES`), real content-aware cut detection, no
   model weights or network needed. Real integration tests found a
   genuine behavior worth documenting: the default `min_scene_len`
   (15 frames) merges cuts closer together than ~1.5s; exposed as a
   tunable constructor argument with a test proving it actually works.
2. **`sceneforge.contrib.whisper`** — `WhisperTranscribeProvider`
   (`Capability.TRANSCRIBE`), real `faster-whisper` integration with
   the model dependency-injected (`docs/adr/0010`) rather than
   constructed internally, since model construction would require
   Hugging Face Hub network access unavailable in this environment.
   Ten unit tests, zero network calls. Also the first genuine use of
   `SyncProviderAdapter` for its intended purpose.
3. **`docs/guides/ADDING_A_PROVIDER.md`** — the checklist that didn't
   exist when this project had zero real providers and was clearly
   missing once it had three; written using all three as worked
   examples, including the anti-patterns this project itself hit and
   fixed.
4. **`examples/end_to_end/analyze_video.py`** now runs two real
   providers (frame extraction + scene detection) against a real
   video, verified by actually running it: correctly detects an exact
   1.5s scene cut, correctly caches on a second run.
5. Corrected `docs/architecture/DOMAIN_MODEL.md`'s "Pipeline" section,
   which described multi-provider composition as if implemented; it
   isn't yet — the doc now says so explicitly rather than describing
   the target shape as current reality.
6. `docs/specifications/REGISTRY_SPEC.md` now documents the real,
   working `Registry.by_capability()` API and flags that `Registry`
   and `Pipeline` are not yet wired together (a real, previously
   undocumented gap).

### Verification

- **227 tests passing** (up from 211 at the start of this pass — 16
  new tests: 6 for scene detection, 10 for transcription).
- **`mypy --strict`**: no errors across 60 source files (one
  `[[tool.mypy.overrides]]` added for `scenedetect`, which ships no
  type stubs).
- **`ruff check`**: all checks pass.
- The end-to-end example was actually executed against a real
  generated video during this pass, not just written — see the
  session transcript for output.

## Pass 2 (Genesis Sprint 2): Architectural resilience + first real capability

### Fixed
1. **`Pipeline` now does what ADR-0003 claims** — timing, retries,
   error wrapping into `ProviderExecutionError`, `ProcessingContext`
   threading for cancellation.
2. **`CapabilityRegistry` replaces global mutable state** — injectable,
   isolated-by-default for tests, no more `_CAPABILITY_MEDIA_MAP`.
3. **`ArtifactStore` (`FileArtifactStore`, `InMemoryArtifactStore`)** —
   content-addressable caching keyed by media identity + provider name
   + version. `Pipeline(..., store=...)` checks before running a
   provider, writes after a successful run.
4. **`AsyncProvider` / `AsyncPipeline`** — timeout via
   `asyncio.wait_for`, retry with backoff, bounded concurrency via
   `run_many()`, per-item failure isolation via `BatchResult`.
5. **`Media.evolve()` + `MediaEnricher` protocol** — the previously
   undocumented "how does placeholder metadata become real metadata on
   an immutable object" gap now has a concrete, tested answer.
6. **`provider_protocol.Provider` declares its full contract** —
   `name`/`version`/`capabilities`/`run()`, not just `run()`. A
   `run()`-only class no longer incorrectly satisfies `isinstance()`.
7. **Plugin discovery via entry points** —
   `PluginRegistry.discover()` finds installed plugins automatically;
   manual `.register()` still available for in-process construction.
8. **First real (non-stub) capability**: `sceneforge.contrib.ffmpeg`
   (`FFprobeEnricher`, `FFmpegFrameExtractionProvider`), integration
   tested against a real synthetic video generated by ffmpeg itself.
9. **Doc/code drift corrected**: `ARTIFACT_SPEC.md`'s fictional
   required-fields list, `MEDIA_SPEC.md`'s "delegated to Providers"
   claim, `NEXT_TASK.md`'s nonexistent `sceneforge/ir/` /
   `sceneforge/capabilities/` paths.
10. **Philosophy doc sprawl reduced**: `MANIFESTO.md`, `NORTH_STAR.md`,
    `CORE_PRINCIPLES.md`, `TEN_COMMANDMENTS.md` (four overlapping
    restatements) consolidated into one `VISION.md`. Previously-empty
    `NAMING_CONVENTIONS.md`/`STYLE_GUIDE.md` filled in with the
    conventions the codebase already follows.
11. `pyproject.toml`: dropped the stale Python 3.10 classifier
    (`requires-python` has been `>=3.11` since StrEnum was adopted);
    aligned `ruff`'s `target-version` to match.

### Verification

- **211 tests passing** (up from 163 at the start of this pass —
  48 new tests covering storage, pipeline resilience, async pipeline,
  plugin discovery, `Media.evolve()`, enrichment, and real ffmpeg
  integration).
- **`mypy --strict`**: no errors across 54 source files.
- **`ruff check`**: all checks pass.

## Pass 1: Surface-level cleanup

1. Removed unused `base_provider.py`.
2. Replaced bare `ValueError` with `InvalidNameError`/
   `InvalidMetadataError` (`SceneForgeError` subclasses).
3. Eliminated wildcard imports in package `__init__.py`; added explicit
   `__all__`.
4. Added CI (`ruff`, `mypy`, `pytest --cov`).
5. Expanded test coverage (registry edge cases, naming/metadata
   validation, `IdentityProvider.capabilities`).
6. Added `Capability.FRAME_EXTRACTION` to the enum (implemented for
   real in Pass 2, via `sceneforge.contrib.ffmpeg`).

## Next Steps

See `.ai/NEXT_TASK.md` for the live, prioritized list. Highest-value
item: build the first real Application — a script that takes a real
processed video's `Entity` data and produces genuinely useful output,
proving `docs/philosophy/VISION.md`'s own success definition for the
first time.
