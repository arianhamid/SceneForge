# Provider Layer

## Purpose

The provider package defines the contract for processing media into artifacts.

## Design Principles

- Protocol-based (structural typing)
- Immutable after construction
- Pure: no mutation, no state, no side effects
- Standard library only

## Provider Protocol

The `Provider` protocol defines the contract for processing media objects.

```python
from typing import Protocol

class Provider(Protocol):
    def run(self, media: Media) -> list[Artifact]:
        ...
```

Any class with a `run()` method returning `list[Artifact]` participates.
Implementations don't need to inherit from this protocol.

## Pipeline as Orchestration Boundary

The `Pipeline` class is the single entry point for processing media through providers. It accepts `Media` objects and returns `Artifact` instances, providing a clean orchestration layer.

```python
from sceneforge.core.pipeline import Pipeline
from sceneforge.contrib.identity import IdentityProvider

pipeline = Pipeline(provider=IdentityProvider())
artifacts = pipeline.run(media)
```

Pipeline is designed as a single-provider orchestrator in Phase 1.5. Provider composition (chaining) will be added in Phase 5.

## Capability Validation

Pipeline validates media compatibility before execution. Each capability is registered with the media types it supports, and Pipeline checks that the media type is compatible with the provider's capabilities.

### How It Works

1. When a Pipeline is created, default capability-to-media mappings are registered automatically.
2. Before executing `provider.run(media)`, Pipeline validates that the media type is compatible with the provider's capabilities.
3. If incompatible, Pipeline raises `IncompatibleMediaError`.
4. If a provider has no capabilities, all media types are accepted.

### Capability-to-Media Mapping

```python
from sceneforge.core.pipeline import register_capability_media
from sceneforge.core.capability import Capability
from sceneforge.media.image import ImageMedia

# Register that CAPTION capability supports ImageMedia
register_capability_media(Capability.CAPTION, {ImageMedia})
```

### IncompatibleMediaError

Raised when media is incompatible with provider capabilities:

```python
from sceneforge.core.exceptions import IncompatibleMediaError

try:
    pipeline.run(audio_media)  # Provider only supports images
except IncompatibleMediaError as e:
    print(f"Provider '{e.provider}' cannot process '{e.media_type}'")
    print(f"Capabilities: {e.capabilities}")
```

### Default Registrations

The following capabilities are registered by default:
- **Image/Video capabilities**: CAPTION, OCR, FACE_DETECTION, OBJECT_DETECTION, EMBEDDING
- **Video-only capabilities**: DETECT_SCENES, FRAME_EXTRACTION
- **Audio capabilities**: TRANSCRIBE, AUDIO_ANALYSIS
- **Cross-media capabilities**: EMBEDDING (Image, Video, Audio), TRANSCRIBE (Audio, Video)

## IdentityProvider

The simplest provider, useful for testing pipeline architecture.

```python
from sceneforge.contrib.identity import IdentityProvider

provider = IdentityProvider()
artifacts = provider.run(image)
```

## IdentityArtifact

Artifact representing successful provider execution.

```python
@dataclass(frozen=True, slots=True)
class IdentityArtifact(Artifact[None]):
    media_id: UUID
    kind: ArtifactKind = ArtifactKind.ARTIFACT
    provider: str = "unknown"
```

## Usage

```python
from sceneforge.core.pipeline import Pipeline
from sceneforge.contrib.identity import IdentityProvider
from sceneforge.media import ImageMedia

provider = IdentityProvider()
pipeline = Pipeline(provider=provider)
image = ImageMedia(name="photo.jpg", width=1920, height=1080, fmt="JPEG")
artifacts = pipeline.run(image)
```

## Constraints

- No external dependencies
- No decoding logic
- No lazy loading
- No hidden state
- Providers are immutable after construction
