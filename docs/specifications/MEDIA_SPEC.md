# Media Layer

## Purpose

The media package provides immutable domain objects representing media resources.

These classes contain no decoding logic. Processing is delegated to Providers.

## Design Principles

- Immutable (`frozen=True, slots=True`)
- Standard library only
- Explicit types
- No hidden state
- No lazy loading

## Types

### Media

Base class for all media types.

```python
@dataclass(frozen=True, slots=True)
class Media:
    name: str
    id: UUID = field(default_factory=uuid4)
    metadata: dict[str, Any] = field(default_factory=dict)
```

### ImageMedia

Represents an image resource.

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class ImageMedia(Media):
    width: int
    height: int
    fmt: str
```

Properties:
- `aspect_ratio` → float
- `pixel_count` → int

### VideoMedia

Represents a video resource.

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class VideoMedia(Media):
    duration: float
    codec: str
    fps: float
```

Properties:
- `frame_count` → int

### AudioMedia

Represents an audio resource.

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class AudioMedia(Media):
    duration: float
    sample_rate: int
    channels: int
    bit_depth: int = 16
```

## Factory Methods

Convenience classmethods for common construction patterns:

- `ImageMedia.from_dimensions(width, height, fmt, **kwargs)` — create from dimensions without pre-computing pixel counts
- `VideoMedia.from_file(path, **kwargs)` — create from a file path (technical metadata is placeholder until a `MediaEnricher` runs)
- `VideoMedia.from_path(path)` — shorthand alias for `from_file`
- `AudioMedia.from_file(path, **kwargs)` — create from a file path (technical metadata is placeholder until a `MediaEnricher` runs)

## Correcting placeholder metadata: Media.evolve()

Media is immutable, so nothing may ever be mutated in place — including
turning placeholder technical metadata into real metadata. `evolve()` is
the sanctioned path: it returns a new instance of the same concrete
type with given fields replaced, merging (not replacing) the `metadata`
dict:

```python
video = VideoMedia(name="movie.mp4", duration=0.0, codec="unknown", fps=0.0)
enriched = video.evolve(duration=120.0, codec="h264", fps=24.0)

enriched is not video       # True -- new instance
enriched.id == video.id     # True -- same logical media, corrected facts
video.duration               # 0.0 -- original is untouched
```

In practice this is called by a `MediaEnricher`
(`sceneforge/core/enrichment.py`), not directly by application code —
see `sceneforge.contrib.ffmpeg.FFprobeEnricher` for the reference
implementation, and `docs/specifications/PROVIDER_SPEC.md`'s
"MediaEnricher" section for how it plugs into `Pipeline`.

## Usage

```python
from sceneforge.media import ImageMedia, VideoMedia, AudioMedia

image = ImageMedia(name="photo.jpg", width=1920, height=1080, fmt="JPEG")
video = VideoMedia(name="movie.mp4", duration=120.0, codec="h264", fps=30.0)
audio = AudioMedia(name="sound.wav", duration=30.0, sample_rate=44100, channels=2)
```

## Constraints

- No external dependencies (no PIL, OpenCV, ffmpeg, NumPy)
- No decoding logic
- No lazy loading
- No hidden state
- `metadata` is wrapped in `MappingProxyType` at init, making it truly immutable after construction

## MediaLoader Protocol

The `MediaLoader` protocol defines the contract for loading media objects.

```python
from typing import Protocol

class MediaLoader(Protocol):
    def load(self) -> Media:
        ...
```

Any class with a `load()` method returning `Media` participates.
Implementations don't need to inherit from this protocol.

## Local File Loaders

Type-specific loaders for loading media from the local filesystem:

- `LocalImageLoader(path)` → `ImageMedia`
- `LocalVideoLoader(path)` → `VideoMedia`
- `LocalAudioLoader(path)` → `AudioMedia`

### Usage

```python
from sceneforge.media import LocalImageLoader, LocalVideoLoader, LocalAudioLoader

image = LocalImageLoader("photo.jpg").load()
video = LocalVideoLoader("movie.mp4").load()
audio = LocalAudioLoader("sound.wav").load()
```

### Path Handling

Loaders accept `str | os.PathLike[str]` and normalize to `pathlib.Path`.

### Error Handling

Loaders raise framework-specific exceptions:

- `MediaNotFoundError` — file does not exist
- `UnsupportedMediaError` — file extension not supported
- `InvalidMediaError` — media data is corrupted
- `MediaIOError` — I/O error during access

### Metadata

Loaders extract inexpensive, stable metadata:
- Identity: filename, extension
- File system: size_bytes, modified_at, source
- Format-specific fields (width/height, codec/fps, sample_rate/channels): return placeholder values; real extraction is delegated to a `MediaEnricher`, not a `Provider` — see "Correcting placeholder metadata" above and `sceneforge/core/enrichment.py`. (An earlier version of this document said "Providers"; that was never actually implemented anywhere and conflated two different concerns.)

Note: Loaders provide filesystem metadata and detect format (e.g., via magic bytes for images), but media-specific fields use placeholder values because extracting them requires decoding. Use a `MediaEnricher` (e.g. `sceneforge.contrib.ffmpeg.FFprobeEnricher` for video) to populate these fields via `Pipeline(..., enricher=...)`.

### Design Principles

- Type-specific loaders (single responsibility)
- Return Media objects, never raw bytes
- Never expose third-party types in public API
- Test with real fixture files, not mocks
