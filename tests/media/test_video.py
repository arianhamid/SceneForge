from pathlib import Path
import pytest
from sceneforge.media.video import VideoMedia


def test_video_media_construction():
    video = VideoMedia(
        name="movie.mp4",
        duration=120.5,
        codec="h264",
        fps=30.0,
    )

    assert video.name == "movie.mp4"
    assert video.duration == 120.5
    assert video.codec == "h264"
    assert video.fps == 30.0


def test_video_media_is_immutable():
    video = VideoMedia(name="movie.mp4", duration=120.0, codec="h264", fps=30.0)

    with pytest.raises(AttributeError):
        video.duration = 0.0  # type: ignore[misc]


def test_video_media_from_file():
    video = VideoMedia.from_file("movie.mp4", duration=120.0, codec="h264", fps=30.0)

    assert isinstance(video.name, str)
    assert video.duration == 120.0


def test_video_media_frame_count():
    video = VideoMedia(name="movie.mp4", duration=10.0, codec="h264", fps=30.0)

    assert video.frame_count == 300


def test_video_media_from_path():
    video = VideoMedia.from_path(Path("movie.mp4"), duration=60.0, codec="h265", fps=24.0)

    assert video.name == "movie.mp4"