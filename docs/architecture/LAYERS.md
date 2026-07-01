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

# Layer 1 — Providers

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

---

# Layer 2 — Artifacts

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

# Layer 3 — Knowledge Builders

Knowledge Builders merge artifacts into reusable entities.

Examples

Character Builder

Location Builder

Dialogue Builder

Object Builder

Scene Builder

Timeline Builder

Knowledge Builders may merge information from many providers.

---

# Layer 4 — Knowledge Graph

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

# Layer 5 — Intelligence

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

# Layer 6 — Applications

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

These rules keep SceneForge modular and replaceable.

---

# Golden Rule

Understanding flows upward.

Configuration flows downward.

Never the opposite.
