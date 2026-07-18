# Project State

Live snapshot — update this when the state actually changes. See
`.ai/NEXT_TASK.md` for the active, prioritized task list.

## Current Sprint

Genesis Sprint 12: four consecutive spikes found no gap in Layer 5.
Pivoting to the first real Application — the actual point of this
framework, per `docs/philosophy/VISION.md`'s own success definition.

## Completed

- Layers 0-3 (Media, Runtime, Providers, Artifacts) implemented and
  tested (308 tests, `ruff check` clean, `mypy --strict` clean across
  73 source files).
- Four real providers across two capability domains:
  `sceneforge.contrib.ffmpeg`, `sceneforge.contrib.scenedetect`,
  `sceneforge.contrib.whisper` (video/audio), `sceneforge.contrib.opencv`
  (image, ADR-0015).
- **Layer 4, three real Knowledge Builders**: `SceneGroupingBuilder`
  (ADR-0011), `SceneFaceBuilder` (cross-domain, ADR-0016),
  `SceneMergeBuilder` (cross-builder merge, ADR-0018). Plus
  `SceneSequenceBuilder` (ADR-0013).
- **`EntityStore` measured sufficient four separate times**, at real
  scale, for four differently-shaped questions: targeted lookup
  (ADR-0014, 0.125s / 11,700 entities), cross-domain correlation
  (ADR-0016), cross-builder merge (ADR-0018), and full-library
  cross-video aggregation (ADR-0019, 0.391s / 23,600 entities / 400
  movies). No index, backend, or graph library added — none of the
  four measurements called for one.
- Registry/Pipeline RFC closed (ADR-0017).
- Runnable end-to-end example
  (`examples/end_to_end/analyze_video.py`): full chain including
  cross-domain face detection and cross-builder merging.
- Documentation: `docs/philosophy/VISION.md`, `NAMING_CONVENTIONS.md`/
  `STYLE_GUIDE.md`, ADRs 0006-0019, `docs/guides/ADDING_A_PROVIDER.md`,
  corrected fictional content across several specs.

## Known Problems

- Layers 5-7 (Knowledge Graph, Intelligence, Applications) do not
  exist as dedicated infrastructure — but four consecutive real
  measurements (ADR-0012, 0014, 0018, 0019) found no gap that would
  require building them as such. `Entity` + `EntityStore` + plain
  Python iteration has answered every real question asked of it so
  far. This is evidence, not proof it'll hold forever.
- `Pipeline` composition (chaining several providers into one ordered
  flow) doesn't exist — a multi-step flow means one `Pipeline` per
  provider, composed in application code.
- `FileArtifactStore`/`FileEntityStore` are plain JSON-per-key
  directories. Measured sufficient at real scale (ADR-0014, ADR-0019);
  a real backend decision stays deferred until a measurement shows
  it's needed.
- `WhisperTranscribeProvider` has never run against real
  `WhisperModel` weights in this environment (no Hugging Face Hub
  access). Logic is fully unit-tested against a structurally-
  compatible fake (ADR-0010); verify against real weights before
  relying on it in production.
- `OpenCVFaceDetectionProvider` has never run against a real face
  photograph in this environment (no network access to fetch one).
  Mechanics and the negative path are genuinely tested (ADR-0015);
  verify against a real photo before relying on it in production.
- `CAPTION`/`OCR`/`OBJECT_DETECTION` remain registered capabilities
  with zero real implementations (`FACE_DETECTION` is now real).
- **No Application exists yet.** Everything built through Sprint 11 is
  infrastructure — real, tested, measured infrastructure, but nothing
  a person would actually run to get something they want out of a
  movie. This is Sprint 12's actual priority.
- `ArtifactStore` (unlike `EntityStore` as of ADR-0014) still has no
  `keys()`/enumeration method. Not needed by anything real yet.

## Architectural Decisions

See `docs/adr/`. Notable ones, most recent first:

- ADR-0019: Cross-video aggregation (a full-library scan, not a
  targeted lookup) also needs no new infrastructure — measured
  (0.391s / 23,600 entities / 400 movies). Fourth consecutive
  confirmation, deliberately tested with a differently-shaped question
  than the prior three specifically to make the result meaningful.
- ADR-0018: Cross-builder entity merging reuses `RelationshipBuilder`
  — no new persistence concept needed.
- ADR-0017: `Registry`/`Pipeline` wiring closed as unnecessary after
  six sprints with zero real callers needing runtime provider
  selection.
- ADR-0016: Cross-domain Knowledge Builders correlate via an Artifact
  field the provider already carries (`source_frame_path`), not a new
  builder Protocol.
- ADR-0015: Face detection ships real with no dependency injection
  needed (bundled Haar cascade weights) — refines ADR-0010. Also
  closed a real gap: `ImageMedia` had no enricher since Sprint 1.
- ADR-0014: Relationship querying (targeted lookup) doesn't need new
  infrastructure — measured (0.125s / 11,700 entities). Also added
  `EntityStore.keys()`, a real, previously-missing capability.
- ADR-0013: Entity relationships reuse the `Entity` shape for
  representation, but need a separate `RelationshipBuilder` Protocol
  from `KnowledgeBuilder`.
- ADR-0012: Entity persistence is a separate `EntityStore`, not a
  shared generic with `ArtifactStore`.
- ADR-0011: The first Knowledge Builder groups by time overlap only.
- ADR-0010: Model-backed providers needing *downloaded* weights take
  the model as a constructor argument (dependency injection). ADR-0015
  refined this: providers with *bundled* weights don't need it.
- ADR-0009 through ADR-0006: async providers, artifact persistence,
  injectable capability registry, complete Provider Protocol contract.

## Open RFCs

- What does `Media.evolve()` mean for cache invalidation across
  multiple enrichers? Still open, still low priority — the only
  carried-over open question left.
- Cross-video querying, cross-builder merging, Registry/Pipeline
  wiring — all **closed**, see ADR-0019, ADR-0018, ADR-0017
  respectively. Listed here only as a record of resolution.

## Future Ideas

- A CLI (`sceneforge run <file> --providers frame_extraction,detect_scenes,face_detection`)
  now that there are four real providers worth chaining.
- A SQLite-backed `ArtifactStore`/`EntityStore` (or a real graph
  library) if a future measurement ever shows linear scan isn't
  enough — four measurements running (ADR-0014, 0018, 0019) have found
  it currently is.
- A DNN-based face detector (better accuracy than Haar cascades) using
  ADR-0010's injection pattern, once accuracy actually matters for a
  real use case.
- Extend `ArtifactStore` with `keys()` to match `EntityStore`
  (ADR-0014) if a real query need for artifacts ever arises.
- A third capability domain provider (`CAPTION`/`OCR`), only once the
  first real Application (Sprint 12) creates a concrete need for
  richer entity content — not added speculatively.

## Immediate Goal

Build the first real Application: a script that takes a real processed
video's `Entity` data and produces genuinely useful output — proving
`docs/philosophy/VISION.md`'s own success definition for the first
time, not just the infrastructure underneath it.
