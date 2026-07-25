"""
Tests for AsyncPipeline: timeout, retry, bounded concurrency, and
partial-failure isolation in run_many().

Written against plain asyncio.run() (no pytest-asyncio dependency)
since this repo's test suite otherwise only needs pytest itself.
"""

import asyncio
from unittest.mock import patch

import pytest

from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.async_pipeline import AsyncPipeline
from sceneforge.core.async_provider import SyncProviderAdapter
from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import (
    IncompatibleMediaError,
    ProviderExecutionError,
    ProviderTimeoutError,
)
from sceneforge.core.storage import InMemoryArtifactStore
from sceneforge.media.audio import AudioMedia
from sceneforge.media.image import ImageMedia
from sceneforge.runtime.analysis_run import AnalysisRun, StageOutcome


class AsyncCountingProvider:
    def __init__(self, name="async-counting", version="1.0.0"):
        self._name = name
        self._version = version
        self.calls = 0

    @property
    def name(self):
        return self._name

    @property
    def version(self):
        return self._version

    @property
    def capabilities(self):
        return frozenset()

    @property
    def execution_fingerprint(self):
        return ""

    async def run(self, media):
        self.calls += 1
        return [
            Artifact(kind=ArtifactKind.ARTIFACT, provider=self.name, payload=self.calls)
        ]


class AsyncFailingProvider:
    @property
    def name(self):
        return "async-failing"

    @property
    def version(self):
        return "1.0.0"

    @property
    def capabilities(self):
        return frozenset()

    async def run(self, media):
        raise RuntimeError("boom")


class AsyncSlowProvider:
    def __init__(self, delay: float):
        self.delay = delay

    @property
    def name(self):
        return "async-slow"

    @property
    def version(self):
        return "1.0.0"

    @property
    def capabilities(self):
        return frozenset()

    async def run(self, media):
        await asyncio.sleep(self.delay)
        return [Artifact(kind=ArtifactKind.ARTIFACT, provider=self.name)]


def _image(name="test.jpg"):
    return ImageMedia(name=name, width=10, height=10, fmt="JPEG")


def test_async_pipeline_basic_run():
    async def _run():
        pipeline = AsyncPipeline(provider=AsyncCountingProvider())
        return await pipeline.run(_image())

    result = asyncio.run(_run())
    assert len(result) == 1


def test_async_pipeline_wraps_errors():
    async def _run():
        pipeline = AsyncPipeline(provider=AsyncFailingProvider())
        await pipeline.run(_image())

    with pytest.raises(ProviderExecutionError):
        asyncio.run(_run())


def test_async_pipeline_timeout():
    async def _run():
        pipeline = AsyncPipeline(
            provider=AsyncSlowProvider(delay=0.2), timeout_seconds=0.01
        )
        await pipeline.run(_image())

    with pytest.raises(ProviderTimeoutError):
        asyncio.run(_run())


def test_async_pipeline_run_many_bounds_concurrency():
    async def _run():
        max_in_flight = 0
        in_flight = 0

        class TrackingProvider:
            @property
            def name(self):
                return "tracking"

            @property
            def version(self):
                return "1.0.0"

            @property
            def capabilities(self):
                return frozenset()

            async def run(self, media):
                nonlocal in_flight, max_in_flight
                in_flight += 1
                max_in_flight = max(max_in_flight, in_flight)
                await asyncio.sleep(0.01)
                in_flight -= 1
                return [Artifact(provider=self.name)]

        pipeline = AsyncPipeline(provider=TrackingProvider(), max_concurrency=2)
        items = [_image(f"frame_{i}.jpg") for i in range(6)]
        batch = await pipeline.run_many(items)
        return batch, max_in_flight

    batch, max_in_flight = asyncio.run(_run())
    assert batch.all_succeeded
    assert len(batch.successes) == 6
    assert max_in_flight <= 2


def test_async_pipeline_run_many_isolates_failures():
    async def _run():
        class SelectiveProvider:
            @property
            def name(self):
                return "selective"

            @property
            def version(self):
                return "1.0.0"

            @property
            def capabilities(self):
                return frozenset()

            async def run(self, media):
                if media.name == "bad.jpg":
                    raise RuntimeError("this scene is corrupt")
                return [Artifact(provider=self.name)]

        pipeline = AsyncPipeline(provider=SelectiveProvider())
        items = [_image("good1.jpg"), _image("bad.jpg"), _image("good2.jpg")]
        return await pipeline.run_many(items)

    batch = asyncio.run(_run())
    assert not batch.all_succeeded
    assert len(batch.successes) == 2
    assert len(batch.failures) == 1


def test_sync_provider_adapter_delegates_to_shared_executor():
    executor_calls = []

    class ImmediateExecutorLoop:
        def run_in_executor(self, executor, function, media):
            executor_calls.append((executor, function, media))

            async def _invoke():
                return function(media)

            return _invoke()

    class SyncProvider:
        @property
        def name(self):
            return "sync-wrapped"

        @property
        def version(self):
            return "1.0.0"

        @property
        def capabilities(self):
            return frozenset()

        def run(self, media):
            return [Artifact(provider=self.name)]

    async def _run():
        adapter = SyncProviderAdapter(SyncProvider())
        pipeline = AsyncPipeline(provider=adapter)
        return await pipeline.run(_image())

    with patch(
        "sceneforge.core.async_provider.asyncio.get_running_loop",
        return_value=ImmediateExecutorLoop(),
    ):
        result = asyncio.run(_run())

    assert len(result) == 1
    assert result[0].provider == "sync-wrapped"
    assert len(executor_calls) == 1
    assert executor_calls[0][0] is None


def test_sync_provider_adapter_propagates_executor_error():
    class ImmediateExecutorLoop:
        def run_in_executor(self, executor, function, media):
            async def _invoke():
                return function(media)

            return _invoke()

    class BrokenSyncProvider:
        @property
        def name(self):
            return "broken-sync"

        @property
        def version(self):
            return "1.0.0"

        @property
        def capabilities(self):
            return frozenset()

        def run(self, media):
            raise RuntimeError("worker failed")

    async def _run():
        adapter = SyncProviderAdapter(BrokenSyncProvider())
        return await adapter.run(_image())

    with (
        patch(
            "sceneforge.core.async_provider.asyncio.get_running_loop",
            return_value=ImmediateExecutorLoop(),
        ),
        pytest.raises(RuntimeError, match="worker failed"),
    ):
        asyncio.run(_run())


class AsyncImageOnlyProvider:
    """Only accepts ImageMedia -- used to trigger a real SKIPPED outcome."""

    @property
    def name(self):
        return "async-image-only"

    @property
    def version(self):
        return "1.0.0"

    @property
    def capabilities(self):
        return frozenset({Capability.CAPTION})

    @property
    def execution_fingerprint(self):
        return ""

    async def run(self, media):
        return [Artifact(kind=ArtifactKind.CAPTION, provider=self.name)]


def test_async_analysis_run_records_a_fresh_success():
    async def _run():
        pipeline = AsyncPipeline(AsyncCountingProvider())
        analysis_run = AnalysisRun()
        await pipeline.run(_image(), analysis_run=analysis_run)
        return analysis_run

    analysis_run = asyncio.run(_run())

    assert len(analysis_run.records) == 1
    record = analysis_run.records[0]
    assert record.outcome == StageOutcome.ATTEMPTED
    assert record.cache_hit is False


def test_async_analysis_run_records_a_cache_hit():
    async def _run():
        store = InMemoryArtifactStore()
        pipeline = AsyncPipeline(AsyncCountingProvider(), store=store)
        media = _image()
        analysis_run = AnalysisRun()
        await pipeline.run(media, analysis_run=analysis_run)
        await pipeline.run(media, analysis_run=analysis_run)
        return analysis_run

    analysis_run = asyncio.run(_run())

    assert len(analysis_run.records) == 2
    assert analysis_run.records[0].cache_hit is False
    assert analysis_run.records[1].cache_hit is True


def test_async_analysis_run_records_a_failure_and_still_raises():
    async def _run():
        pipeline = AsyncPipeline(AsyncFailingProvider())
        analysis_run = AnalysisRun()
        with pytest.raises(ProviderExecutionError):
            await pipeline.run(_image(), analysis_run=analysis_run)
        return analysis_run

    analysis_run = asyncio.run(_run())

    assert len(analysis_run.records) == 1
    assert analysis_run.records[0].outcome == StageOutcome.FAILED
    assert "boom" in analysis_run.records[0].error


def test_async_analysis_run_records_a_skip_and_still_raises():
    async def _run():
        pipeline = AsyncPipeline(AsyncImageOnlyProvider())
        audio = AudioMedia(
            name="sound.wav", duration=1.0, sample_rate=44100, channels=1
        )
        analysis_run = AnalysisRun()
        with pytest.raises(IncompatibleMediaError):
            await pipeline.run(audio, analysis_run=analysis_run)
        return analysis_run

    analysis_run = asyncio.run(_run())

    assert len(analysis_run.records) == 1
    assert analysis_run.records[0].outcome == StageOutcome.SKIPPED


def test_run_many_shares_one_analysis_run_across_the_batch():
    async def _run():
        pipeline = AsyncPipeline(AsyncCountingProvider(), max_concurrency=2)
        analysis_run = AnalysisRun()
        media_items = [_image(f"scene_{i}.jpg") for i in range(4)]
        await pipeline.run_many(media_items, analysis_run=analysis_run)
        return analysis_run

    analysis_run = asyncio.run(_run())

    assert len(analysis_run.records) == 4
    assert all(r.outcome == StageOutcome.ATTEMPTED for r in analysis_run.records)


def test_async_pipeline_run_without_analysis_run_is_unaffected():
    async def _run():
        pipeline = AsyncPipeline(AsyncCountingProvider())
        return await pipeline.run(_image())

    artifacts = asyncio.run(_run())
    assert len(artifacts) == 1
