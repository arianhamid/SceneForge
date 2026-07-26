# SceneForge Domain Model

## Purpose

This document defines the vocabulary of SceneForge.

Every contributor should use these terms consistently.

---

# Movie

A source of narrative information.

Contains media only.

---

# Artifact

An immutable observation extracted directly from media.

Examples

Frame

Transcript

OCR

Caption

Embedding

---

# Entity

A reusable concept derived from artifacts.

Examples

Character

Location

Object

Scene

Chapter

Event

Dialogue

---

# Relationship

A connection between entities. Represented as an `Entity` with kind
`RELATIONSHIP`, whose `parents` point at the two related entity ids
(see `docs/adr/0013-entity-relationships.md`) — no separate base type.

Real, shipped example (`sceneforge.knowledge`)

`SceneSequenceBuilder` — "Scene N precedes Scene N+1", built by a
`RelationshipBuilder` (a distinct Protocol from `KnowledgeBuilder`;
see `docs/architecture/LAYERS.md`'s "Two builder shapes, not one").

Illustrative examples (not yet implemented)

Character appears in Scene.

Dialogue belongs to Character.

Scene occurs at Location.

Object used by Character.

---

# Knowledge Graph

The complete set of entities and relationships.

Acts as the central understanding of a movie.

No dedicated `WorldModel`/graph-database type exists for this yet —
`Entity` + `EntityStore` + `iter_all_entities()`/`find_related()` have
been measured sufficient for every real query asked of them so far
(targeted lookup, cross-domain correlation, cross-builder merge,
full-library aggregation — see ADR-0012, 0014, 0018, 0019). See
`docs/adr/0021-world-model-vocabulary.md` for the trigger condition
that would justify building one.

---

# The Understanding Ladder

A finer-grained vocabulary for "how raw video becomes understanding,"
adopted from a vision document proposing SceneForge model movies the
way people remember them — not as pixels, but as evidence resolving
into an increasingly complete, provenance-tracked picture. See
`docs/adr/0021-world-model-vocabulary.md` for the full reasoning.
Each rung is marked with what's real today and what would need to
exist first to build the next one for real.

**Evidence** — everything directly observable: frame, scene cut,
transcript segment, detected face, OCR text. *Maps to `Artifact`.
Real, seven feature providers deep
(`sceneforge.contrib.ffmpeg/scenedetect/whisper/opencv/tesseract/
transformers_caption/transformers_object_detection`).*

**Facts** — evidence converted into objective, higher-level statements
("character speaks", "door opens"). *Real, with two independent real
inputs: `TransformersCaptionProvider` (`Capability.CAPTION`) produces a
`CaptionArtifact`, `TransformersObjectDetectionProvider`
(`Capability.OBJECT_DETECTION`) produces an `ObjectDetectionArtifact`,
and `FactExtractionBuilder` converts either into a `Fact`-kind `Entity`
(`EntityKind.FACT`), proven end to end against a real ffmpeg-generated
image through a real `Pipeline`
(`tests/knowledge/test_fact_extraction_integration.py`). The second
provider was built specifically to test generalization: the
one-Artifact-to-one-Fact shape held, but statement synthesis didn't
(a caption's text is already the statement; a detection's `label`
needs a template), so the builder dispatches per artifact type rather
than assuming one code path fits both. Still deliberately narrow: no
deduplication of overlapping detections or repeated captions, no
synthesis across caption/detection/OCR text describing the same
frame, no contradiction handling.*

**Entities** — persistent objects that survive across scenes (a
character, a location) and accumulate evidence over time. *Partially
real: `Entity` exists and `EntityKind.CHARACTER`/`LOCATION` are
forward-declared in the enum, but nothing yet re-identifies "the same
character" across non-adjacent scenes — that needs a real recognition/
embedding provider, which doesn't exist yet. `SceneEntity` (via
`SceneGroupingBuilder`/`SceneFaceBuilder`) is real today.*

**Events** — structured compositions of Facts ("John enters room").
*Not built. Unblocked now that Facts exists (however narrowly), but no
real Event-producing Knowledge Builder exists yet — per
`.ai/NEXT_TASK.md`, deliberately not started until a real need
motivates its shape, the same discipline that produced
`FactExtractionBuilder`'s narrow scope rather than a speculative one.*

**State** — how entities change over time ("door: closed → opened →
destroyed"). *Not built. Blocked on Events existing first.*

**Relationships** — typed, evolving connections between entities
(friend, suspects, protects — not just "connected"). *Partially real:
`EntityKind.RELATIONSHIP` + `RelationshipBuilder` exist
(`SceneSequenceBuilder` for scene ordering, `SceneMergeBuilder` for
same-scene merging) but nothing yet represents entity-to-entity social/
narrative relationships, which need Entities (characters) to exist
first.*

**Intentions** — inferred, not extracted ("John wants money"). *Not
built. Requires an LLM-reasoning step over a populated graph that
has Facts now, but no Events or persistent cross-scene character/
location Entities to reason over.*

**Narrative** — story structure (setup, rising action, climax).
*Not built, same blocker as Intentions.*

**Themes** — the highest level (redemption, corruption, identity).
*Not built, same blocker. The vision document's own words: "These
should never affect lower layers" — a constraint worth keeping
whenever this layer is eventually built, so a theme inference can
never quietly reshape what a lower layer claims it observed.*

**Provenance** — every fact remembers why the system believes it,
and evidence is never deleted, only superseded by new evidence with
its own provenance. *Real today: `Entity.provenance` (`Provenance`
dataclass: builder, source_artifact_ids, confidence), and structurally
true throughout — `Artifact`/`Entity` are immutable and `parents`
always traces a conclusion back to what produced it.*

---

# Intelligence

Information inferred from knowledge.

Examples

Character Growth

Theme

Conflict

Foreshadowing

Narrative Pace

Symbolism

Roughly corresponds to the Understanding Ladder's Intentions/
Narrative/Themes rungs above — kept here as the original, coarser
term; the ladder is the more precise vocabulary going forward.

---

# Capability

A framework feature.

Examples

Caption Image

Transcribe Audio

Detect Scenes

Track Characters

Summarize Story

Every provider implements capabilities.

Applications never call providers directly.

---

# Provider

An implementation of one or more capabilities.

Real, shipped examples (`sceneforge.contrib`)

FFmpegFrameExtractionProvider (FRAME_EXTRACTION)

PySceneDetectProvider (DETECT_SCENES)

WhisperTranscribeProvider (TRANSCRIBE)

Illustrative examples (not yet implemented)

QwenVLProvider

JoyCaptionProvider

ClaudeProvider

GeminiProvider

Providers are interchangeable.

---

# Pipeline

Orchestrates one Provider's execution against one Media object:
validate compatibility, optionally enrich, optionally check a cache,
run the provider, optionally populate the cache.

**Not yet implemented**: chaining several providers/capabilities into
one ordered sequence, as the diagram below describes. Today, building
a multi-step flow (extract frames, then detect scenes, then
transcribe) means constructing one `Pipeline` per provider and calling
each in application code — see `examples/end_to_end/analyze_video.py`
for exactly that pattern. True composition (a `Pipeline` that owns the
whole sequence) is real future work, not yet started; see
`docs/specifications/PROVIDER_SPEC.md`'s "Pipeline as Orchestration
Boundary" section and `.ai/PROJECT_STATE.md`'s open questions. The
diagram below describes the *target* shape, not the current one.

Example (target shape, not yet implemented)

Movie

↓

Extract Frames

↓

Transcribe

↓

Detect Scenes

↓

Caption

↓

Knowledge Builder

↓

Reasoners

↓

Applications

---

# Plugin

An installable package that extends SceneForge.

Plugins may provide

Capabilities

Providers

Reasoners

Applications

Knowledge Builders

Plugins should require zero modifications to the core framework.

---

# Principle

Every architectural discussion should use this vocabulary.

Avoid inventing new terms when an existing domain concept already exists.
