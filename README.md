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
sceneforge/          # Core Python package
  core/              # Core abstractions (Artifact, Provider, Registry)
docs/
  architecture/      # Architectural decisions and layer definitions
  philosophy/        # Project values and principles
  specifications/    # Technical specifications
tests/               # Test suite
examples/            # Usage examples
.ai/                 # AI agent context and decisions
```

---

## Installation

```bash
git clone https://github.com/arianhamid/SceneForge.git
cd SceneForge
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -e ".[dev]"
```

---

## Development

### Environment Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate it
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -e ".[dev]"
```

### Environment Variables

Copy `.env` to `.env.local` and configure your API keys:

```bash
cp .env .env.local
# Edit .env.local with your settings
```

### Running Tests

```bash
pytest tests/ -v
```

### Running Tests with Coverage

```bash
pytest tests/ --cov=sceneforge --cov-report=html
```

### Linting

```bash
ruff check sceneforge/
ruff format sceneforge/
```

### Type Checking

```bash
mypy sceneforge/
```

---

## Project Status

🚧 **Genesis Phase**

The framework architecture is being implemented. Core abstractions are in place:

- [x] Artifact base class (immutable, serializable)
- [x] Provider abstraction
- [x] Capability system
- [x] Provider Registry
- [ ] Knowledge Graph
- [ ] Intelligence Engine
- [ ] Pipeline system
- [ ] Plugin ecosystem

---

## Documentation

- [Architecture Overview](docs/architecture/OVERVIEW.md)
- [Domain Model](docs/architecture/DOMAIN_MODEL.md)
- [Layered Architecture](docs/architecture/LAYERS.md)
- [Core Principles](docs/philosophy/CORE_PRINCIPLES.md)
- [Manifesto](docs/philosophy/MANIFESTO.md)
- [Engineering Philosophy](.ai/ENGINEERING_PHILOSOPHY.md)
- [Artifact Specification](docs/specifications/ARTIFACT_SPEC.md)
- [Provider Specification](docs/specifications/PROVIDER_SPEC.md)
- [Registry Specification](docs/specifications/REGISTRY_SPEC.md)

---

## Contributing

We welcome contributors interested in:

- Computer Vision
- Large Language Models
- Video Understanding
- Knowledge Graphs
- Software Architecture
- Open Source

Please read [CONTRIBUTING.md](CONTRIBUTING.md) and our [Code of Conduct](docs/philosophy/COMMUNITY_PRINCIPLES.md) before submitting a pull request.

---

## Philosophy

SceneForge is not built around today's models.

It is built around tomorrow's understanding.

---

## License

Apache-2.0

---

## Project Motto

> **Movies are not just videos. They are worlds waiting to be understood.**
