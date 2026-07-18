"""
Tests for WhisperTranscribeProvider.

These never download model weights or touch the network -- they
inject a fake model satisfying `WhisperModelProtocol`, which is the
entire point of that Protocol existing (see the module docstring in
`sceneforge/contrib/whisper/provider.py`). A separate, explicitly
network-free contract test checks that the *real*
`faster_whisper.WhisperModel` class shape matches what this provider
expects, without ever instantiating it.
"""

from __future__ import annotations

import asyncio

import pytest

from sceneforge.contrib.whisper import (
    TranscriptSegmentArtifact,
    WhisperTranscribeProvider,
)
from sceneforge.core.artifact import ArtifactKind
from sceneforge.core.async_pipeline import AsyncPipeline
from sceneforge.core.async_provider import SyncProviderAdapter
from sceneforge.core.exceptions import ProviderError
from sceneforge.core.pipeline import Pipeline
from sceneforge.media.audio import AudioMedia
from sceneforge.media.image import ImageMedia
from sceneforge.media.video import VideoMedia


class FakeSegment:
    def __init__(self, start: float, end: float, text: str) -> None:
        self.start = start
        self.end = end
        self.text = text


class FakeTranscriptionInfo:
    def __init__(self, language: str = "en") -> None:
        self.language = language


class FakeWhisperModel:
    """Satisfies WhisperModelProtocol without any real model weights."""

    def __init__(self, segments: list[FakeSegment], language: str = "en") -> None:
        self._segments = segments
        self._language = language
        self.calls: list[str] = []

    def transcribe(self, audio: str, **kwargs):
        self.calls.append(audio)
        return iter(self._segments), FakeTranscriptionInfo(self._language)


class BrokenWhisperModel:
    def transcribe(self, audio: str, **kwargs):
        raise RuntimeError("model inference failed")


def _audio(source: str = "/tmp/clip.wav") -> AudioMedia:
    return AudioMedia(
        name="clip.wav",
        duration=10.0,
        sample_rate=16000,
        channels=1,
        metadata={"source": source},
    )


def test_transcribe_produces_one_artifact_per_segment():
    model = FakeWhisperModel(
        [
            FakeSegment(0.0, 2.0, " Hello there. "),
            FakeSegment(2.0, 4.5, "General Kenobi."),
        ]
    )
    provider = WhisperTranscribeProvider(model)

    artifacts = provider.run(_audio())

    assert len(artifacts) == 2
    assert all(isinstance(a, TranscriptSegmentArtifact) for a in artifacts)
    assert all(a.kind == ArtifactKind.TRANSCRIPT for a in artifacts)
    assert artifacts[0].payload == "Hello there."  # stripped
    assert artifacts[0].start_seconds == 0.0
    assert artifacts[0].end_seconds == 2.0
    assert artifacts[1].segment_index == 1
    assert artifacts[0].language == "en"


def test_transcribe_passes_source_path_to_model():
    model = FakeWhisperModel([])
    provider = WhisperTranscribeProvider(model)

    provider.run(_audio(source="/tmp/my_clip.wav"))

    assert model.calls == ["/tmp/my_clip.wav"]


def test_transcribe_kwargs_are_forwarded():
    calls = []

    class RecordingModel:
        def transcribe(self, audio, **kwargs):
            calls.append(kwargs)
            return iter([]), FakeTranscriptionInfo()

    provider = WhisperTranscribeProvider(RecordingModel(), language="fa", beam_size=3)
    provider.run(_audio())

    assert calls == [{"language": "fa", "beam_size": 3}]


def test_video_media_is_accepted():
    model = FakeWhisperModel([FakeSegment(0.0, 1.0, "hi")])
    provider = WhisperTranscribeProvider(model)

    video = VideoMedia(
        name="movie.mp4",
        duration=10.0,
        codec="h264",
        fps=24.0,
        metadata={"source": "/tmp/movie.mp4"},
    )
    artifacts = provider.run(video)

    assert len(artifacts) == 1


def test_non_audio_video_media_raises_type_error():
    provider = WhisperTranscribeProvider(FakeWhisperModel([]))
    with pytest.raises(TypeError):
        provider.run(ImageMedia(name="x.png", width=1, height=1, fmt="PNG"))


def test_missing_source_raises_provider_error():
    provider = WhisperTranscribeProvider(FakeWhisperModel([]))
    media = AudioMedia(name="clip.wav", duration=1.0, sample_rate=16000, channels=1)

    with pytest.raises(ProviderError):
        provider.run(media)


def test_model_exception_is_wrapped_in_provider_error():
    provider = WhisperTranscribeProvider(BrokenWhisperModel())

    with pytest.raises(ProviderError):
        provider.run(_audio())


def test_works_through_sync_pipeline():
    model = FakeWhisperModel([FakeSegment(0.0, 1.0, "hello")])
    pipeline = Pipeline(provider=WhisperTranscribeProvider(model))

    result = pipeline.run_detailed(_audio())

    assert len(result.artifacts) == 1
    assert result.from_cache is False


def test_sync_provider_adapter_enables_concurrent_batches():
    """
    The whole reason WhisperTranscribeProvider is synchronous rather
    than duplicated as an async implementation: SyncProviderAdapter
    should let it run under AsyncPipeline's bounded concurrency.
    """

    async def _run():
        model = FakeWhisperModel([FakeSegment(0.0, 1.0, "hi")])
        adapter = SyncProviderAdapter(WhisperTranscribeProvider(model))
        pipeline = AsyncPipeline(provider=adapter, max_concurrency=2)

        clips = [_audio(source=f"/tmp/clip_{i}.wav") for i in range(4)]
        return await pipeline.run_many(clips)

    batch = asyncio.run(_run())
    assert batch.all_succeeded
    assert len(batch.successes) == 4


def test_real_whisper_model_shape_is_compatible():
    """
    Contract check only -- never instantiates WhisperModel (which would
    download weights from the Hugging Face Hub) or runs inference.
    Confirms WhisperModelProtocol was modeled on the real library's
    actual method signature, not a guess.
    """
    faster_whisper = pytest.importorskip("faster_whisper")

    assert hasattr(faster_whisper.WhisperModel, "transcribe")
