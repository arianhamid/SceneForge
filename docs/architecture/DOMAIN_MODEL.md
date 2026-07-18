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
