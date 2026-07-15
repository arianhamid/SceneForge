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
             Runtime Infrastructure
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

# Runtime Infrastructure

Runtime infrastructure provides execution-time services for media processing.

## Media Runtime

The media runtime layer handles decoding of media into representations:

- **ImageRepresentation** — Decoded image pixels with metadata
- **VideoRepresentation** — Video metadata with on-demand frame access
- **AudioRepresentation** — Audio metadata with on-demand chunk access

## Decoder Protocol

The `Decoder` protocol defines how media is decoded into representations:

```python
class Decoder(Protocol):
    def decode(self, media: Media) -> Any: ...
```

Providers request decoding via the Decoder protocol, never performing it directly.

This separation ensures:
- No OpenCV-specific APIs leak into providers
- Decoding can be swapped (OpenCV, FFmpeg, etc.)
- Providers focus on AI model execution, not media I/O

## StubDecoder

A reference implementation for testing that returns placeholder representations without actual decoding.

---

## Capability Validation

Pipeline validates media compatibility before provider execution:

1. **Capability Registration**: Each capability is registered with the media types it supports.
2. **Media Validation**: Before calling `provider.run(media)`, Pipeline checks if the media type is compatible with the provider's capabilities.
3. **Error Handling**: If incompatible, Pipeline raises `IncompatibleMediaError` with provider and media details.
4. **Zero Capability Check in Providers**: Providers contain zero capability checks — validation is handled entirely by Pipeline.

```python
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.exceptions import IncompatibleMediaError

pipeline = Pipeline(provider=ImageProvider())
try:
    pipeline.run(audio_media)  # ImageProvider doesn't support audio
except IncompatibleMediaError as e:
    print(f"Cannot process {e.media_type} with {e.provider}")
```

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
