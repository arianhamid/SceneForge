# 🎬 SceneForge

> **The Open Framework for Narrative Intelligence**

> **Movies are not just videos. They are worlds waiting to be understood.**

---

## Vision

SceneForge is an open-source framework for extracting, organizing, reasoning about, and reusing knowledge from movies and videos.

Unlike traditional video AI pipelines that stop after generating captions or JSON, SceneForge builds a structured understanding of visual stories that can power many different applications.

A movie is analyzed once.

Its understanding becomes reusable forever.

---

## Why SceneForge?

Today's AI video pipelines are tightly coupled to individual models.

```
Movie
   ↓
Model
   ↓
Application
```

Changing the model often requires rewriting the application.

SceneForge introduces a new architecture.

```
Movie
   ↓
Artifacts
   ↓
Knowledge
   ↓
Intelligence
   ↓
Applications
```

Applications never depend on AI models.

Applications depend on knowledge.

---

## Goals

- Understand movies instead of merely describing frames.
- Build reusable structured knowledge.
- Remain model-agnostic.
- Support local and cloud AI providers.
- Encourage reproducible research.
- Serve as the foundation for many applications.

---

## Example Applications

- Comic generation
- Storyboard generation
- Novel generation
- Movie search
- Character tracking
- Scene understanding
- Dataset generation
- RAG pipelines
- Educational tools
- Video analytics

---

## Core Concepts

### Artifacts

Immutable outputs produced directly from media.

Examples:

- Frames
- Audio
- Transcript
- OCR
- Scene cuts
- Embeddings

---

### Knowledge

Structured facts extracted from artifacts.

Examples:

- Characters
- Locations
- Objects
- Dialogue
- Events
- Relationships

---

### Intelligence

Reasoning performed on knowledge.

Examples:

- Character arcs
- Story arcs
- Themes
- Motivations
- Emotional progression
- Narrative structure

---

## Framework Architecture

```
                 Applications
                       │
               Intelligence Engine
                       │
               Knowledge Graph
                       │
              Extraction Pipelines
                       │
                  Artifacts
                       │
                    Movie
```

---

## Design Principles

- Architecture before implementation.
- Knowledge before generation.
- Capabilities before models.
- Immutable artifacts.
- Plugin-first architecture.
- Framework over workflows.
- Documentation as a first-class feature.

---

## Repository Structure

```
sceneforge/
docs/
specs/
plugins/
applications/
tests/
benchmarks/
examples/
.ai/
```

---

## Current Status

🚧 Genesis

The framework architecture is currently being implemented.

MovieToComic serves as the research prototype that validates many of SceneForge's ideas before they become generic framework capabilities.

---

## Documentation

See:

- docs/
- specs/
- .ai/

---

## Contributing

We welcome contributors interested in:

- Computer Vision
- Large Language Models
- Video Understanding
- Knowledge Graphs
- Software Architecture
- Open Source

---

## Philosophy

SceneForge is not built around today's models.

It is built around tomorrow's understanding.

---

## License

Apache-2.0 (planned)

---

## Project Motto

> **Movies are not just videos. They are worlds waiting to be understood.**
