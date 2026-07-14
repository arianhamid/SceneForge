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
- `VideoMedia.from_file(path, **kwargs)` — create from a file path (requires a Provider to extract codec/fps metadata)
- `VideoMedia.from_path(path)` — shorthand alias for `from_file`
- `AudioMedia.from_file(path, **kwargs)` — create from a file path (requires a Provider to extract sample rate/channels metadata)

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
