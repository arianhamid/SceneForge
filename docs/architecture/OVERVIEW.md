# Architecture Overview

SceneForge is organized as a layered architecture.

```
                 Applications
                       │
              Intelligence Engine
                       │
                Knowledge Graph
                       │
              Knowledge Builders
                       │
                   Artifacts
                       │
                    Providers
                       │
                 Source Media
```

Each layer has a single responsibility.

---

# Layer 1 — Providers

Providers interact with external systems.

Examples:

- Whisper
- Qwen-VL
- JoyCaption
- OCR engines
- Scene detectors

Providers never communicate directly with applications.

---

# Layer 2 — Artifacts

Artifacts are immutable observations extracted from media.

Examples:

- Frame
- Audio segment
- Transcript
- Scene cut
- OCR result
- Caption
- Face detection

Artifacts contain facts, not reasoning.

---

# Layer 3 — Knowledge Builders

Knowledge builders transform artifacts into reusable entities.

Examples:

- Character identification
- Location clustering
- Dialogue association
- Object tracking
- Event extraction

---

# Layer 4 — Knowledge Graph

The knowledge graph stores structured information about the story.

Nodes may include:

- Characters
- Locations
- Objects
- Events
- Scenes
- Chapters

Relationships connect these entities over time.

---

# Layer 5 — Intelligence

Reasoners derive higher-level understanding.

Examples:

- Character arcs
- Emotional progression
- Narrative pacing
- Themes
- Symbolism
- Causality

---

# Layer 6 — Applications

Applications consume intelligence.

Applications never perform extraction directly.

This separation allows the same understanding to power many outputs.
