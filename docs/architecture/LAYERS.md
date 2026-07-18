# SceneForge Layered Architecture

## Purpose

This document defines the architectural layers of SceneForge.

Every module belongs to exactly one layer.

Layers may only depend on layers below them.

No exceptions.

---

# Why Layers?

Without strict boundaries, AI projects quickly become difficult to extend.

Providers begin calling applications.

Applications begin parsing provider JSON.

Knowledge becomes duplicated.

Replacing one model requires rewriting everything.

SceneForge prevents this by enforcing a layered architecture.

---

# Layer 0 — Media

External inputs.

Examples

- Movies
- TV Shows
- YouTube Videos
- Image Sequences
- Audio
- Livestreams

SceneForge never modifies media.

---

# Layer 1 — Runtime Infrastructure

Runtime infrastructure provides execution-time services for media processing.

## Media Runtime

Handles decoding of media into representations:

- **ImageRepresentation** — Decoded image pixels with metadata
- **VideoRepresentation** — Video metadata with on-demand frame access
- **AudioRepresentation** — Audio metadata with on-demand chunk access

## Decoder Protocol

Defines how media is decoded into representations:

```python
class Decoder(Protocol):
    def decode(self, media: Media) -> Any: ...
```

Providers request decoding via the Decoder protocol, never performing it directly.

## Responsibilities

✓ Decode media into representations
✓ Provide execution-time data structures
✓ Isolate providers from media I/O details

## Forbidden

✗ Contain AI model logic
✗ Make assumptions about media content
✗ Communicate with applications

---

# Layer 2 — Providers

Providers communicate with external AI systems.

Examples

- Whisper
- Qwen2.5-VL
- JoyCaption
- OCR
- SceneDetect
- Face Recognition
- Object Detection

Responsibilities

✓ Execute AI models

✓ Normalize outputs

✓ Produce Artifacts

Forbidden

✗ Build knowledge

✗ Make assumptions

✗ Call applications

## A note on real vs. placeholder Media

Loaders (Layer 1) are deliberately cheap — filesystem-level only. A
freshly-loaded `VideoMedia` has placeholder technical metadata
(`duration=0.0`, `codec="unknown"`). Before a Provider should trust
that metadata, a `MediaEnricher` (`sceneforge/core/enrichment.py`)
corrects it via `Media.evolve()`, returning a new immutable instance
rather than mutating anything. `Pipeline(..., enricher=...)` runs this
automatically before validation. See
`sceneforge.contrib.ffmpeg.FFprobeEnricher` for the reference
implementation.

## Sync and async Providers

Most Providers here are I/O- or GPU-bound (a model call, a subprocess).
`Provider` (sync) and `AsyncProvider` (async, `sceneforge/core/async_provider.py`)
are the same four-member contract — `name`, `version`, `capabilities`,
`run()` — so either shape can plug into the layer. `SyncProviderAdapter`
wraps a sync `Provider` for use under `AsyncPipeline`'s bounded
concurrency (`run_many()`), which matters once a movie has more than a
couple of scenes to process.

---

# Layer 3 — Artifacts

Artifacts are immutable observations.

Examples

Frame

TranscriptSegment

SceneCut

Caption

OCRResult

Embedding

FaceDetection

AudioSegment

Properties

- Immutable
- Timestamped
- Serializable
- Reproducible

Artifacts never contain reasoning.

---

# Persistence (cross-cutting, not a numbered layer)

Added in Genesis Sprint 2 — this section didn't exist when the layer
list above was written, which is exactly the problem: the North Star
("a movie is analyzed once, reused forever" — `docs/philosophy/VISION.md`)
requires *something* to remember artifacts across runs, and nothing
did.

`ArtifactStore` (`sceneforge/core/storage.py`) is not slotted in as
"Layer 3.5" because it isn't a stage data flows through once — it's a
side-channel every layer at Artifacts (3) and above may read from and
write to: `Pipeline` checks it before calling a Provider and writes to
it after; the future Knowledge Graph (Layer 5) is itself a persistent
store, of Knowledge Builder output rather than raw Artifacts, and may
end up backed by a different technology entirely (see `.ai/PROJECT_STATE.md`'s
open RFCs).

Responsibilities

✓ Cache Provider output, keyed by media identity + provider name + version

✓ Make "already analyzed" a queryable fact, not an assumption

Forbidden

✗ Contain reasoning or knowledge-graph-shaped data (that's Layer 5)

✗ Be assumed reliable across a provider version bump — a version
change is a deliberate cache-invalidation signal, not a bug

---

# Layer 4 — Knowledge Builders

Knowledge Builders merge artifacts into reusable entities.

Real, shipped example (`sceneforge.knowledge`)

`SceneGroupingBuilder` — groups `FrameExtractionArtifact` and
`TranscriptSegmentArtifact` into the `SceneCutArtifact` time ranges
they overlap, producing one `SceneEntity` per detected scene. See
`docs/guides/ADDING_A_PROVIDER.md`'s sibling considerations and
`sceneforge/knowledge/scene_grouping_builder.py`'s module docstring
for why this is deliberately the smallest useful builder rather than
an attempt at full scene understanding — it exists to prove the
`Artifact -> Entity` contract against real provider output
(`tests/knowledge/test_scene_grouping_integration.py`), not to be the
last word on what a "scene" means.

Illustrative examples (not yet implemented)

Character Builder

Location Builder

Dialogue Builder

Object Builder

Timeline Builder

Knowledge Builders may merge information from many providers. They
read Artifacts and produce Entities; they never call Providers or
Applications, and never modify the Artifacts they read (see
`sceneforge/knowledge/builder.py`'s `KnowledgeBuilder` Protocol).

## Two builder shapes, not one

Building a real relationship (`SceneSequenceBuilder`, linking
consecutive scenes — see `docs/adr/0013-entity-relationships.md`)
surfaced that Layer 4 actually has two distinct stages, not the single
`Artifacts -> Entities` step this section originally implied:

```
Artifacts -> KnowledgeBuilder.build()      -> Entities  (e.g. SceneGroupingBuilder)
Entities  -> RelationshipBuilder.relate()  -> Entities  (e.g. SceneSequenceBuilder)
```

`RelationshipBuilder` (`sceneforge/knowledge/relationship_builder.py`)
is a separate Protocol from `KnowledgeBuilder` because its input is
Entities (the output of an earlier builder stage), not Artifacts —
forcing both through one Protocol would have meant lying about the
input type. A relationship is itself just an `Entity`
(`EntityKind.RELATIONSHIP`) whose `parents` point at the two related
Entity ids rather than Artifact ids; no new base type was needed for
the representation, only for the builder-stage distinction.

`RelationshipBuilder` isn't only for "different entities relate to
each other" (`SceneSequenceBuilder`'s scene ordering) — it also covers
"these entities describe the same thing and should be combined"
(`SceneMergeBuilder`, `sceneforge/knowledge/scene_merge_builder.py`,
`docs/adr/0018-scene-merge-builder.md`). Two different `KnowledgeBuilder`
stages (`SceneGroupingBuilder`, `SceneFaceBuilder`) each produce their
own `SCENE` entity for the same scene; `SceneMergeBuilder` combines
them into one, namespaced by source builder name, using the same
`Entity -> Entity` Protocol shape with no new type or persistence
concept needed.

## Querying entities and relationships

`EntityStore` (`sceneforge/knowledge/storage.py`) is a cache keyed by
exact `entity_build_key()`, not a queryable database — `get(key)`
requires already knowing the key. `iter_all_entities(store)` /
`find_related(store, entity_id)` are the query primitives built on top
of `EntityStore.keys()`: enumerate everything, filter in memory.
Measured against a synthetic 300-movie / 11,700-entity dataset, a
`find_related()` call completes in ~0.125s — fast enough that no
index, different backend, or graph library has been added. Measured
again, differently, at 400-movie / 23,600-entity scale for a genuine
full-library aggregation (rank every movie by face count — no shortcut
available, every entity must be read): ~0.391s. Four consecutive
real measurements (targeted lookup, cross-domain correlation,
cross-builder merge, cross-video aggregation) have now found the
existing `Entity`/`EntityStore`/plain-Python-iteration shape
sufficient. See `docs/adr/0014-relationship-query-spike.md` and
`docs/adr/0019-cross-video-query-spike.md` for the measurements and
the conditions under which either conclusion should be revisited.

---

# Layer 5 — Knowledge Graph

The central database of understanding.

Contains

Characters

Locations

Objects

Events

Scenes

Dialogues

Relationships

Timeline

Everything inside SceneForge eventually converges here.

---

# Layer 6 — Intelligence

Reasoners operate exclusively on the Knowledge Graph.

Examples

Story Arc

Character Arc

Theme Detection

Emotion Flow

Conflict Analysis

Cause and Effect

Symbolism

Reasoners never call providers.

---

# Layer 7 — Applications

Applications consume Intelligence.

Examples

Comic Generator

Novel Generator

Storyboard Generator

Search Engine

Dataset Builder

Video QA

Game Export

Applications never perform extraction.

---

# Dependency Rules

Allowed

Media

↓

Runtime Infrastructure

↓

Providers

↓

Artifacts

↓

Knowledge

↓

Intelligence

↓

Applications

Forbidden

Applications → Providers

Providers → Applications

Reasoners → Providers

Artifacts → Intelligence

Knowledge → Media

Runtime Infrastructure → Applications

These rules keep SceneForge modular and replaceable.

---

# Golden Rule

Understanding flows upward.

Configuration flows downward.

Never the opposite.
