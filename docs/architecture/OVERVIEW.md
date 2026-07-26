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
                   Artifacts  ◄──┐
                       │         │ (cache read/write,
                    Providers    │  see Persistence below)
                       │         │
             Runtime Infrastructure
                       │
                 Source Media

  Persistence (ArtifactStore) is cross-cutting, not a rung on this
  ladder -- Pipeline and every layer at Artifacts and above can read
  from and write to it. See docs/architecture/LAYERS.md's
  "Persistence (cross-cutting, not a numbered layer)" section.
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

1. **Capability Registration**: A `CapabilityRegistry` maps each capability to
   the media types it supports. `Pipeline` takes one via constructor
   injection (defaulting to a shared, pre-populated registry) rather than
   reading from global state — see `docs/adr/0007-injectable-capability-registry.md`.
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

Need a different (or isolated, e.g. for tests) set of rules? Pass your own:

```python
from sceneforge.core.capability_registry import CapabilityRegistry
from sceneforge.core.capability import Capability

registry = CapabilityRegistry()
registry.register(Capability.CAPTION, {ImageMedia})
pipeline = Pipeline(provider=ImageProvider(), capability_registry=registry)
```

## Enrichment: from placeholder to authoritative Media

Loaders are cheap and filesystem-only, so a freshly-loaded `VideoMedia`
has placeholder technical metadata (`duration=0.0`, `codec="unknown"`).
A `MediaEnricher` corrects this before the Provider ever sees it, by
returning a new `Media` instance via `Media.evolve()` (Media is
immutable — nothing is ever mutated in place):

```python
from sceneforge.contrib.ffmpeg import FFprobeEnricher

pipeline = Pipeline(provider=FrameExtractionProvider(), enricher=FFprobeEnricher())
result = pipeline.run_detailed(media)  # result.media has real duration/fps/codec
```

## Caching: making "analyze once" literal

Pass an `ArtifactStore` and `Pipeline` looks up a cached result (keyed
on media identity + provider name + version) before running the
provider, and persists a fresh result after a successful run:

```python
from sceneforge.core.storage import FileArtifactStore

pipeline = Pipeline(provider=TranscribeProvider(), store=FileArtifactStore("./cache"))
first = pipeline.run_detailed(media)  # runs the provider
second = pipeline.run_detailed(media)  # from_cache=True, provider not re-run
```

See `docs/adr/0008-artifact-persistence.md` for why this exists and what it deliberately doesn't do yet.

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
