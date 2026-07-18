"""
Integration test for SceneGroupingBuilder against REAL provider output.

This is the proof the whole point of Sprint 3 was building toward:
real ffmpeg frame extraction + real scenedetect scene detection +
(fake-model, network-free) whisper transcription, all run through
their actual Pipeline/Provider machinery, fed into the Knowledge
Builder that was designed against imagined artifact shapes until this
test proved (or would have caught) whether those shapes were right.

The whisper model is a fake (see tests/contrib/test_whisper_transcribe.py
for why) -- everything else in this test is completely real.
"""

from __future__ import annotations

import dataclasses
import shutil
import subprocess
from pathlib import Path

import pytest

from sceneforge.contrib.ffmpeg import FFmpegFrameExtractionProvider, FFprobeEnricher
from sceneforge.contrib.scenedetect import PySceneDetectProvider
from sceneforge.contrib.whisper import WhisperTranscribeProvider
from sceneforge.core.pipeline import Pipeline
from sceneforge.knowledge import EntityKind, SceneGroupingBuilder
from sceneforge.media.audio import AudioMedia
from sceneforge.media.video_loader import LocalVideoLoader

pytest.importorskip("scenedetect")

FFMPEG_AVAILABLE = (
    shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
)
pytestmark = pytest.mark.skipif(
    not FFMPEG_AVAILABLE, reason="ffmpeg/ffprobe not on PATH"
)


class FakeWhisperSegment:
    def __init__(self, start: float, end: float, text: str) -> None:
        self.start = start
        self.end = end
        self.text = text


class FakeWhisperInfo:
    language = "en"


class FakeWhisperModel:
    """Deterministic fake standing in for a real WhisperModel (see ADR-0010)."""

    def transcribe(self, audio: str, **kwargs):
        # Pretend the (real, silent) audio track produced two lines of
        # dialogue straddling the video's real cut point.
        return (
            iter(
                [
                    FakeWhisperSegment(0.2, 1.3, "This is the red half."),
                    FakeWhisperSegment(1.8, 2.7, "This is the blue half."),
                ]
            ),
            FakeWhisperInfo(),
        )


@pytest.fixture
def video_with_cut_and_audio(tmp_path: Path) -> Path:
    """A real video: red 1.5s, blue 1.5s, with a real (silent) audio track."""
    path = tmp_path / "scene.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:duration=1.5:size=64x64:rate=10",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:duration=1.5:size=64x64:rate=10",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=16000:cl=mono",
            "-filter_complex",
            "[0:v][1:v]concat=n=2:v=1:a=0[v]",
            "-map",
            "[v]",
            "-map",
            "2:a",
            "-shortest",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        capture_output=True,
        check=True,
        timeout=30,
    )
    return path


def test_knowledge_builder_against_real_provider_output(video_with_cut_and_audio: Path):
    media = LocalVideoLoader(video_with_cut_and_audio).load()
    enricher = FFprobeEnricher()

    frame_result = Pipeline(
        provider=FFmpegFrameExtractionProvider(frame_count=4),
        enricher=enricher,
    ).run_detailed(media)

    scene_result = Pipeline(
        provider=PySceneDetectProvider(), enricher=enricher
    ).run_detailed(media)

    # Transcription runs against the same real video's audio track, but
    # through a fake model -- see module docstring.
    audio_media = AudioMedia(
        name=media.name,
        duration=frame_result.media.duration,
        sample_rate=16000,
        channels=1,
        metadata={"source": frame_result.media.metadata["source"]},
    )
    transcript_result = Pipeline(
        provider=WhisperTranscribeProvider(FakeWhisperModel())
    ).run_detailed(audio_media)

    # The transcript artifacts reference audio_media.id, not media.id --
    # relink them the way a real Knowledge Builder input assembly step
    # would, since frames/scenes came from the video Media and the
    # transcript came from a derived audio Media view of the same movie.
    relinked_transcripts = [
        dataclasses.replace(segment, media_id=media.id)
        for segment in transcript_result.artifacts
    ]

    all_artifacts = [
        *frame_result.artifacts,
        *scene_result.artifacts,
        *relinked_transcripts,
    ]

    entities = SceneGroupingBuilder().build(all_artifacts)

    assert len(entities) == 2
    scene0, scene1 = sorted(entities, key=lambda e: e.metadata["scene_index"])
    assert scene0.kind == EntityKind.SCENE
    assert 1.4 <= scene0.metadata["end_seconds"] <= 1.6
    assert len(scene0.metadata["frame_paths"]) >= 1
    assert len(scene1.metadata["frame_paths"]) >= 1

    all_frame_paths = [*scene0.metadata["frame_paths"], *scene1.metadata["frame_paths"]]
    for frame_path in all_frame_paths:
        assert Path(frame_path).exists()
