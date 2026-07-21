# Provider Layer

## Purpose

The provider package defines the contract for processing media into artifacts.

## Design Principles

- Protocol-based (structural typing) *and* ABC-based (nominal typing) — see
  `docs/adr/0001-provider-protocol.md` for why both exist.
- Immutable after construction
- Pure: no mutation, no state, no side effects
- Standard library only in `sceneforge.core`; external dependencies (ffmpeg,
  model libraries) live in `sceneforge.contrib`, never in core.

## Provider Protocol

The `Provider` protocol declares the full structural contract — every
member `Pipeline` actually depends on, not just `run()` (this was a real
bug, fixed in `docs/adr/0006-provider-protocol-completeness.md`):

```python
from typing import Protocol
from sceneforge.core.capability import Capability

class Provider(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def capabilities(self) -> frozenset[Capability]: ...

    def run(self, media: Media) -> list[Artifact]: ...
```

Any class implementing all four members participates. Implementations
don't need to inherit from this protocol — inheriting from the ABC
`sceneforge.core.provider.Provider` is the more common path and gets you
`isinstance()` checks and IDE support for free, but the Protocol exists
for providers that can't or shouldn't take the inheritance dependency.

**`version` matters beyond documentation**: it's part of the cache key
`Pipeline` derives when an `ArtifactStore` is configured (see below). Bump
it whenever the provider's actual output would change for the same input
— a real model upgrade, a changed prompt, a changed post-processing step.
Forgetting to bump it means stale cached results get served as if they
were fresh.

## AsyncProvider

For I/O- or GPU-bound providers (an STT model, a captioning VLM, a
ComfyUI call), `AsyncProvider` (`sceneforge/core/async_provider.py`) is
the same four-member contract with `run()` declared `async`. Wrap an
existing synchronous `Provider` with `SyncProviderAdapter` rather than
writing two implementations:

```python
from sceneforge.core.async_provider import SyncProviderAdapter
from sceneforge.core.async_pipeline import AsyncPipeline

async_provider = SyncProviderAdapter(MySyncProvider())
pipeline = AsyncPipeline(async_provider, max_concurrency=3, timeout_seconds=120)
batch = await pipeline.run_many(scene_clips)
```

See `docs/adr/0009-async-providers.md`.

## Pipeline as Orchestration Boundary

The `Pipeline` class is the single entry point for processing media
through providers: enrich → validate → check cache → run provider →
populate cache. It accepts `Media` objects and returns `Artifact`
instances.

```python
from sceneforge.core.pipeline import Pipeline
from sceneforge.contrib.identity import IdentityProvider

pipeline = Pipeline(provider=IdentityProvider())
artifacts = pipeline.run(media)
```

`run()` stays a plain `list[Artifact]` for simple callers.
`run_detailed()` also returns timing, retry count, whether the result
came from cache, and the (possibly enriched) `Media` that was actually
processed:

```python
result = pipeline.run_detailed(media)
result.artifacts        # list[Artifact]
result.media             # possibly enriched Media
result.duration_seconds  # 0.0 if from_cache
result.attempts          # 0 if from_cache
result.from_cache
```

Pipeline is still a single-provider orchestrator; provider composition
(chaining several providers' output together) remains a later-phase
concern, now that a real end-to-end example (`.ai/NEXT_TASK.md`) exists
to design chaining against instead of guessing at the shape upfront.

## Capability Validation

Pipeline validates media compatibility before execution, using an
injectable `CapabilityRegistry` rather than global state (see
`docs/adr/0007-injectable-capability-registry.md`):

```python
from sceneforge.core.capability_registry import CapabilityRegistry
from sceneforge.core.capability import Capability
from sceneforge.media.image import ImageMedia

registry = CapabilityRegistry()
registry.register(Capability.CAPTION, {ImageMedia})

pipeline = Pipeline(provider=my_provider, capability_registry=registry)
```

Don't pass one and `Pipeline` uses a shared, pre-populated default
registry covering SceneForge's built-in capabilities — fine for most
callers; construct your own when you need isolation (tests, a plugin
with non-default capabilities).

### IncompatibleMediaError

```python
from sceneforge.core.exceptions import IncompatibleMediaError

try:
    pipeline.run(audio_media)  # Provider only supports images
except IncompatibleMediaError as e:
    print(f"Provider '{e.provider}' cannot process '{e.media_type}'")
    print(f"Capabilities: {e.capabilities}")
```

### Default Registrations

- **Image/Video capabilities**: CAPTION, OCR, FACE_DETECTION, OBJECT_DETECTION
- **Video-only capabilities**: DETECT_SCENES, FRAME_EXTRACTION
- **Audio capabilities**: TRANSCRIBE, AUDIO_ANALYSIS
- **Cross-media capabilities**: EMBEDDING (Image, Video, Audio), TRANSCRIBE (Audio, Video)

## MediaEnricher

Loaders are cheap and produce placeholder technical metadata for some
media types (`VideoMedia.duration == 0.0` until something actually
probes the file). A `MediaEnricher` corrects this by returning a new
`Media` via `Media.evolve()` — never mutating the original:

```python
from sceneforge.contrib.ffmpeg import FFprobeEnricher

pipeline = Pipeline(provider=my_provider, enricher=FFprobeEnricher())
```

`Pipeline` runs the enricher before capability validation, so
validation and the provider both see corrected metadata. See
`docs/adr/0009-async-providers.md`'s sibling, `sceneforge/core/enrichment.py`,
and `docs/architecture/OVERVIEW.md`'s "Enrichment" section.

## Retries and Timeouts

```python
Pipeline(provider=my_provider, max_retries=2, retry_backoff_seconds=0.5)
AsyncPipeline(provider=my_async_provider, max_retries=2, timeout_seconds=30)
```

`max_retries=0` (default) means no retries — a raised exception is
wrapped in `ProviderExecutionError` and raised immediately. Retries use
linear backoff (`retry_backoff_seconds * attempt_number`).

## Caching (ArtifactStore)

```python
from sceneforge.core.storage import FileArtifactStore

pipeline = Pipeline(provider=my_provider, store=FileArtifactStore("./cache"))
```

See `docs/adr/0008-artifact-persistence.md`.

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

## Real Providers Shipped in sceneforge.contrib

Three real, non-stub providers exist so far — use the closest one as a
template for a new provider rather than starting from a blank file.
See `docs/guides/ADDING_A_PROVIDER.md` for the full checklist.

### sceneforge.contrib.ffmpeg — subprocess-backed

`FFmpegFrameExtractionProvider` (capability `FRAME_EXTRACTION`) and its
companion `FFprobeEnricher` shell out to real `ffmpeg`/`ffprobe`
binaries. Integration tested against a real generated video in
`tests/contrib/test_ffmpeg_integration.py`.

```python
from sceneforge.contrib.ffmpeg import FFmpegFrameExtractionProvider, FFprobeEnricher
from sceneforge.media.video_loader import LocalVideoLoader
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.storage import FileArtifactStore

media = LocalVideoLoader("movie.mp4").load()
pipeline = Pipeline(
    provider=FFmpegFrameExtractionProvider(frame_count=12),
    enricher=FFprobeEnricher(),
    store=FileArtifactStore("./cache"),
)
result = pipeline.run_detailed(media)
```

### sceneforge.contrib.scenedetect — algorithmic, no weights

`PySceneDetectProvider` (capability `DETECT_SCENES`) wraps the
`scenedetect` library's content-aware cut detection — no model
weights, no network, so it's real-integration-tested everywhere the
package is installed (`tests/contrib/test_scenedetect_integration.py`).

```python
from sceneforge.contrib.scenedetect import PySceneDetectProvider

pipeline = Pipeline(provider=PySceneDetectProvider(threshold=27.0))
result = pipeline.run_detailed(media)
for cut in result.artifacts:
    print(cut.scene_index, cut.start_seconds, cut.end_seconds)
```

### sceneforge.contrib.whisper — model-backed, dependency-injected

`WhisperTranscribeProvider` (capability `TRANSCRIBE`) wraps
`faster-whisper`. Unlike the two providers above, it needs downloaded
model weights, so the model is *injected* rather than constructed
internally — see `docs/adr/0010-dependency-injected-model-providers.md`
for why, and `tests/contrib/test_whisper_transcribe.py` for how this
makes it fully unit-testable without a GPU or network access.

```python
from faster_whisper import WhisperModel
from sceneforge.contrib.whisper import WhisperTranscribeProvider
from sceneforge.core.async_provider import SyncProviderAdapter
from sceneforge.core.async_pipeline import AsyncPipeline

model = WhisperModel("small", device="cpu", compute_type="int8")
provider = SyncProviderAdapter(WhisperTranscribeProvider(model))
pipeline = AsyncPipeline(provider, max_concurrency=2, timeout_seconds=300)
batch = await pipeline.run_many(scene_audio_clips)  # concurrent, bounded, partial-failure-safe
```

### sceneforge.contrib.opencv — algorithmic, bundled weights, no injection needed

`OpenCVFaceDetectionProvider` (capability `FACE_DETECTION`) uses
OpenCV's bundled Haar cascade classifier — trained weights that ship
*inside* the `opencv-python`/`opencv-python-headless` package, not
downloaded separately. Unlike `sceneforge.contrib.whisper`, this needs
no dependency injection (see `docs/adr/0015-opencv-face-detection.md`
for why "model-backed" doesn't automatically mean "needs injection").
Its companion `OpenCVImageEnricher` fills in real width/height for
`ImageMedia` (a gap that existed since Sprint 1 — `ImageMedia` never
had an enricher the way `VideoMedia` got `FFprobeEnricher`).

```python
from sceneforge.contrib.opencv import OpenCVFaceDetectionProvider, OpenCVImageEnricher
from sceneforge.media.image_loader import LocalImageLoader

media = LocalImageLoader("photo.jpg").load()
pipeline = Pipeline(
    provider=OpenCVFaceDetectionProvider(),
    enricher=OpenCVImageEnricher(),
)
result = pipeline.run_detailed(media)
for face in result.artifacts:
    print(face.x, face.y, face.width, face.height)
```

**Test coverage honesty**: no real face photograph is available in
this environment (no network access to fetch one). Tests prove the
real mechanics and the negative path (zero detections on non-face
images) with certainty; the positive-detection claim is real
production code but unverified here — verify against a real photo
before relying on it in production.

### sceneforge.contrib.tesseract — algorithmic, bundled weights, verified positive detection

`TesseractOCRProvider` (capability `OCR`) wraps the Tesseract OCR
engine — trained language data ships as part of the `tesseract-ocr`
system package, not downloaded separately, the same shape as
`sceneforge.contrib.opencv`. Unlike the whisper and opencv providers,
its positive-detection claim *is* verified in this environment: real
text rendered with a bundled font, read back correctly (see
`docs/adr/0022-real-ocr-provider.md`).

```python
from sceneforge.contrib.tesseract import TesseractOCRProvider
from sceneforge.media.image_loader import LocalImageLoader

media = LocalImageLoader("photo.jpg").load()
pipeline = Pipeline(provider=TesseractOCRProvider())
for word in pipeline.run(media):
    print(word.payload, word.confidence)
```

`SceneTextBuilder` (`sceneforge.knowledge`) correlates OCR text back to
scenes via `source_frame_path`, the same cross-domain pattern
`SceneFaceBuilder` uses (ADR-0016) — confirmed working a second time.

## Constraints

- Core (`sceneforge.core`) has no external dependencies. Real-world
  integrations (ffmpeg, model libraries) live in `sceneforge.contrib`.
- No decoding logic inside a Provider — that's the Runtime layer's job.
- No lazy loading, no hidden state.
- Providers are immutable after construction.
- Every Provider must implement `name`, `version`, `capabilities`, and
  `run()` — see "Provider Protocol" above.
