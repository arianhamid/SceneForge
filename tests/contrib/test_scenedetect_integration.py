"""
Integration tests for the PySceneDetect contrib package.

Unlike a transcription provider, scene detection needs no model
weights or network access, so this runs against real generated video
files everywhere `scenedetect` is installed -- no skip condition
needed beyond the import itself.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

pytest.importorskip("scenedetect")

from sceneforge.contrib.scenedetect import PySceneDetectProvider, SceneCutArtifact
from sceneforge.core.artifact import ArtifactKind
from sceneforge.core.pipeline import Pipeline
from sceneforge.media.video_loader import LocalVideoLoader


def _ffmpeg_available() -> bool:
    import shutil

    return shutil.which("ffmpeg") is not None


pytestmark = pytest.mark.skipif(
    not _ffmpeg_available(), reason="ffmpeg not available on PATH"
)


@pytest.fixture
def video_with_hard_cut(tmp_path: Path) -> Path:
    """
    A real, tiny video with an unmistakable hard cut halfway through:
    2s of a solid red frame, then 2s of a solid blue frame. Each half
    is long enough to clear ContentDetector's default `min_scene_len`
    (15 frames) at this fixture's frame rate, so content-aware
    detection should find exactly one cut at the boundary.
    """
    path = tmp_path / "hard_cut.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:duration=2:size=64x64:rate=10",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:duration=2:size=64x64:rate=10",
            "-filter_complex",
            "[0:v][1:v]concat=n=2:v=1:a=0",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        capture_output=True,
        check=True,
        timeout=30,
    )
    return path


@pytest.fixture
def video_with_brief_cut(tmp_path: Path) -> Path:
    """
    A real video with a cut too brief for scenedetect's *default*
    min_scene_len to register -- 1s red, 1s blue at 10fps (10 frames
    each half, default min_scene_len is 15). Used to prove
    `min_scene_len` is a real, working tunable, not a documented-but-
    unused constructor argument.
    """
    path = tmp_path / "brief_cut.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:duration=1:size=64x64:rate=10",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:duration=1:size=64x64:rate=10",
            "-filter_complex",
            "[0:v][1:v]concat=n=2:v=1:a=0",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        capture_output=True,
        check=True,
        timeout=30,
    )
    return path


@pytest.fixture
def video_without_cuts(tmp_path: Path) -> Path:
    """A real video with no content change at all -- should yield one scene."""
    path = tmp_path / "static.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=green:duration=1:size=64x64:rate=10",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        capture_output=True,
        check=True,
        timeout=30,
    )
    return path


def test_detects_a_real_hard_cut(video_with_hard_cut: Path):
    media = LocalVideoLoader(video_with_hard_cut).load()
    provider = PySceneDetectProvider()

    artifacts = provider.run(media)

    assert len(artifacts) >= 2
    assert all(isinstance(a, SceneCutArtifact) for a in artifacts)
    assert all(a.kind == ArtifactKind.SCENE_CUT for a in artifacts)
    # Scenes should be contiguous and in order.
    for earlier, later in zip(artifacts, artifacts[1:], strict=False):
        assert earlier.scene_index < later.scene_index
        assert earlier.end_seconds <= later.start_seconds + 0.01


def test_static_video_yields_one_scene(video_without_cuts: Path):
    media = LocalVideoLoader(video_without_cuts).load()
    provider = PySceneDetectProvider()

    artifacts = provider.run(media)

    assert len(artifacts) == 1
    assert artifacts[0].scene_index == 0


def test_full_pipeline_with_scenedetect_provider(video_with_hard_cut: Path):
    media = LocalVideoLoader(video_with_hard_cut).load()
    pipeline = Pipeline(provider=PySceneDetectProvider())

    result = pipeline.run_detailed(media)

    assert len(result.artifacts) >= 2
    assert result.attempts == 1
    assert result.from_cache is False


def test_non_video_media_raises_type_error():
    from sceneforge.media.image import ImageMedia

    provider = PySceneDetectProvider()
    with pytest.raises(TypeError):
        provider.run(ImageMedia(name="x.png", width=1, height=1, fmt="PNG"))


def test_min_scene_len_default_merges_brief_cuts(video_with_brief_cut: Path):
    """A cut shorter than the default min_scene_len should not register."""
    media = LocalVideoLoader(video_with_brief_cut).load()
    provider = PySceneDetectProvider()

    artifacts = provider.run(media)

    assert len(artifacts) == 1  # merged into a single scene


def test_min_scene_len_lowered_detects_brief_cuts(video_with_brief_cut: Path):
    """Lowering min_scene_len should surface the same cut the default merges away."""
    media = LocalVideoLoader(video_with_brief_cut).load()
    provider = PySceneDetectProvider(min_scene_len=1)

    artifacts = provider.run(media)

    assert len(artifacts) >= 2
