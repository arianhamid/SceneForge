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

A connection between entities.

Examples

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

Examples

QwenVLProvider

WhisperProvider

JoyCaptionProvider

ClaudeProvider

GeminiProvider

Providers are interchangeable.

---

# Pipeline

An ordered sequence of capabilities.

Example

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
