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
              Knowledge Builders
                       │
                  Artifacts  ◄── ArtifactStore (persistence, cross-cutting)
                       │
                    Providers
                       │
             Runtime Infrastructure
                       │
                    Movie
```

See [Layered Architecture](docs/architecture/LAYERS.md) for the full
picture, including why persistence is cross-cutting rather than a rung
on this ladder.

---

## Design Principles

See [Vision](docs/philosophy/VISION.md) for the full list and the
reasoning behind each. In short:

- Architecture before implementation — but prove it against a real
  external tool before formalizing the next layer.
- Knowledge before generation.
- Capabilities before models.
- Immutable artifacts, explicit corrections (`Media.evolve()`,
  `Artifact.parents`).
- Plugin-first architecture, discoverable via entry points.
- No hidden state.
- Documentation as a first-class feature — and kept honest about what's
  actually implemented, not what's planned.

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
AGENTS.md             # Durable Codex/AI engineering contract
.github/              # CI, dependency updates, and review templates
```

---

## Installation

```bash
git clone https://github.com/arianhamid/SceneForge.git
cd SceneForge
python3.12 -m venv .venv  # Linux/macOS
# py -3.12 -m venv .venv  # Windows
.venv\Scripts\Activate.ps1  # Windows PowerShell
# source .venv/bin/activate  # Linux/macOS
python -m pip install -e ".[dev]"
```

---

## Quick Start

Three real, working providers plus a Knowledge Builder — not stubs:

```python
from sceneforge.media.video_loader import LocalVideoLoader
from sceneforge.contrib.ffmpeg import FFmpegFrameExtractionProvider, FFprobeEnricher
from sceneforge.contrib.scenedetect import PySceneDetectProvider
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.storage import FileArtifactStore
from sceneforge.knowledge import SceneGroupingBuilder

media = LocalVideoLoader("movie.mp4").load()  # placeholder metadata so far
enricher = FFprobeEnricher()                   # fills in real duration/codec/fps
store = FileArtifactStore("./cache")           # analyze once, reuse forever

frames = Pipeline(
    provider=FFmpegFrameExtractionProvider(frame_count=12),
    enricher=enricher,
    store=store,
).run_detailed(media)

scenes = Pipeline(provider=PySceneDetectProvider(), enricher=enricher, store=store).run_detailed(media)

# Knowledge layer: group frames into the scenes they fall within
entities = SceneGroupingBuilder().build([*frames.artifacts, *scenes.artifacts])
for entity in entities:
    print(entity.metadata["scene_index"], len(entity.metadata["frame_paths"]), "frames")
```

Requires `ffmpeg`/`ffprobe` on `PATH` and `pip install "sceneforge[scenedetect]"`.
See [`docs/specifications/PROVIDER_SPEC.md`](docs/specifications/PROVIDER_SPEC.md)
for the full Provider/Pipeline contract (including the `faster-whisper`
transcription provider),
[`docs/guides/ADDING_A_PROVIDER.md`](docs/guides/ADDING_A_PROVIDER.md)
for how to add the next one, and
[`examples/end_to_end/analyze_video.py`](examples/end_to_end/analyze_video.py)
for this exact flow as a runnable script.

---

## Development

### Environment Setup

SceneForge requires the latest Python 3.12 patch release.

```bash
# Create virtual environment
python3.12 -m venv .venv  # Linux/macOS
# py -3.12 -m venv .venv  # Windows

# Activate it
.venv\Scripts\Activate.ps1  # Windows PowerShell
# source .venv/bin/activate  # Linux/macOS

# Install dependencies
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Environment Variables

The framework currently requires no environment variables or API keys. Optional
future integrations must document their own configuration without committing
secrets.

### Running Tests

```bash
python -m pytest -q
```

### Running Tests with Coverage

```bash
make coverage
```

This instruments the complete suite and enforces the 80% project threshold.

### Linting

```bash
python -m ruff check .
python -m ruff format --check .
```

### Type Checking

```bash
python -m mypy --strict sceneforge
```

Run every non-mutating quality gate with `make check`. Codex and other coding
agents should follow [AGENTS.md](AGENTS.md); human contributors using AI should
also read the [AI-assisted development guide](docs/guides/AI_ASSISTED_DEVELOPMENT.md).

---

## Project Status

🚧 **Genesis Phase** — real, but still early. Layers 0-4 (Media, Runtime,
Providers, Artifacts, and Knowledge Builders) are implemented and tested, and
Layer 7 has its first real application (`SceneSummary`). Dedicated Knowledge
Graph and Intelligence infrastructure (Layers 5-6) does not exist because the
current Entity/EntityStore design has covered every measured query so far. See
[`.ai/PROJECT_STATE.md`](.ai/PROJECT_STATE.md)
for the live, honest snapshot — checklists like this one go stale fast,
that file is the one kept current.

- [x] Artifact base class (immutable, serializable, persists via `ArtifactStore`)
- [x] Media base class + `evolve()` for immutable metadata correction
- [x] Provider abstraction (sync `Provider` + async `AsyncProvider`)
- [x] Capability system (injectable `CapabilityRegistry`, no global state)
- [x] Pipeline (validation, enrichment, retries, timing, caching, cancellation)
- [x] Plugin ecosystem (entry-point discovery via `PluginRegistry.discover()`)
- [x] Three real providers, one per shape: `sceneforge.contrib.ffmpeg` (subprocess), `sceneforge.contrib.scenedetect` (algorithmic), `sceneforge.contrib.whisper` (model-backed, dependency-injected)
- [x] Fourth real provider, image domain: `sceneforge.contrib.opencv` (bundled weights, no injection needed — ADR-0015)
- [x] Fifth real provider: `sceneforge.contrib.tesseract` OCR (ADR-0022)
- [x] Utility provider: `MediaHashProvider`
- [x] First Knowledge Builder: `sceneforge.knowledge.SceneGroupingBuilder`, proven against real provider output
- [x] Second Knowledge Builder, cross-domain: `SceneFaceBuilder` (video + image domains — ADR-0016)
- [x] Third Knowledge Builder, OCR correlation: `SceneTextBuilder` (ADR-0022)
- [x] Cross-builder entity merge: `SceneMergeBuilder` (ADR-0018)
- [x] Entity persistence: `EntityStore` (ADR-0012)
- [x] Entity relationships: `RelationshipBuilder`/`SceneSequenceBuilder` (ADR-0013)
- [x] Relationship querying measured at scale: 0.125s / 11,700 entities (ADR-0014)
- [x] Cross-video aggregation measured at scale: 0.391s / 23,600 entities / 400 movies (ADR-0019)
- [x] Registry/Pipeline wiring RFC: closed as unnecessary (ADR-0017)
- [x] First real Application: `SceneSummary` (Sprint 12)
- [ ] First Fact-producing provider and builder (next up — see `.ai/NEXT_TASK.md`)
- [ ] Dedicated Knowledge Graph and Intelligence Engine (no measured need yet)

---

## Documentation

- [مستندات فارسی (Persian Documentation)](docs/fa/README.md) — a full
  educational walkthrough of the project in Persian, written for
  learning the architecture and the Python patterns used, from zero
- [Architecture Overview](docs/architecture/OVERVIEW.md)
- [Domain Model](docs/architecture/DOMAIN_MODEL.md)
- [Layered Architecture](docs/architecture/LAYERS.md)
- [Vision](docs/philosophy/VISION.md)
- [Anti-Goals](docs/philosophy/ANTI_GOALS.md)
- [Engineering Philosophy](.ai/ENGINEERING_PHILOSOPHY.md)
- [Architecture Decision Records](docs/adr/) — start with
  [0007](docs/adr/0007-injectable-capability-registry.md),
  [0008](docs/adr/0008-artifact-persistence.md),
  [0009](docs/adr/0009-async-providers.md),
  [0010](docs/adr/0010-dependency-injected-model-providers.md),
  [0011](docs/adr/0011-first-knowledge-builder-scope.md),
  [0012](docs/adr/0012-entity-persistence.md),
  [0013](docs/adr/0013-entity-relationships.md),
  [0014](docs/adr/0014-relationship-query-spike.md),
  [0015](docs/adr/0015-opencv-face-detection.md),
  [0016](docs/adr/0016-cross-domain-knowledge-builder.md),
  [0017](docs/adr/0017-registry-pipeline-rfc-closed.md),
  [0018](docs/adr/0018-scene-merge-builder.md),
  [0019](docs/adr/0019-cross-video-query-spike.md),
  [0020](docs/adr/0020-stable-api-surface.md),
  [0021](docs/adr/0021-world-model-vocabulary.md),
  [0022](docs/adr/0022-real-ocr-provider.md), and
  [0023](docs/adr/0023-python-3-12-baseline.md) for the most recent
  structural decisions
- [Guide: Adding a Provider](docs/guides/ADDING_A_PROVIDER.md) — start
  here if you're implementing the next capability
- [Media Specification](docs/specifications/MEDIA_SPEC.md)
- [Artifact Specification](docs/specifications/ARTIFACT_SPEC.md)
- [Provider Specification](docs/specifications/PROVIDER_SPEC.md)
- [Plugin Specification](docs/specifications/PLUGIN_SPEC.md)
- [Registry Specification](docs/specifications/REGISTRY_SPEC.md)
- [Runtime Specification](docs/specifications/RUNTIME_SPEC.md)

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
