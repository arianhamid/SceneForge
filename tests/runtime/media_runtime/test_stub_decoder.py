"""Tests for stub decoder."""

from sceneforge.media.audio import AudioMedia
from sceneforge.media.image import ImageMedia
from sceneforge.media.video import VideoMedia
from sceneforge.runtime.media_runtime import StubDecoder
from sceneforge.runtime.media_runtime.audio_representation import AudioRepresentation
from sceneforge.runtime.media_runtime.image_representation import ImageRepresentation
from sceneforge.runtime.media_runtime.video_representation import VideoRepresentation


def test_stub_decoder_image():
    """StubDecoder should decode ImageMedia."""
    decoder = StubDecoder()
    image = ImageMedia(name="test.jpg", width=1920, height=1080, fmt="JPEG")

    result = decoder.decode(image)

    assert isinstance(result, ImageRepresentation)
    assert result.media_id == image.id
    assert result.width == 1920
    assert result.height == 1080


def test_stub_decoder_video():
    """StubDecoder should decode VideoMedia."""
    decoder = StubDecoder()
    video = VideoMedia(
        name="movie.mp4",
        duration=120.0,
        codec="h264",
        fps=30.0
    )

    result = decoder.decode(video)

    assert isinstance(result, VideoRepresentation)
    assert result.media_id == video.id
    assert result.duration == 120.0
    assert result.fps == 30.0


def test_stub_decoder_audio():
    """StubDecoder should decode AudioMedia."""
    decoder = StubDecoder()
    audio = AudioMedia(
        name="sound.wav",
        duration=30.0,
        sample_rate=44100,
        channels=2
    )

    result = decoder.decode(audio)

    assert isinstance(result, AudioRepresentation)
    assert result.media_id == audio.id
    assert result.duration == 30.0
    assert result.sample_rate == 44100
