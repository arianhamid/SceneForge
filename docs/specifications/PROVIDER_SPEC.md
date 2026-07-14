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
