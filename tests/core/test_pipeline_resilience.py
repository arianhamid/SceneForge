"""
Tests for Pipeline features added on top of the original bare
validate-then-run: error wrapping, retries, ProcessingContext
threading, MediaEnricher integration, and ArtifactStore caching.
"""

import pytest

from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.exceptions import (
    EnrichmentError,
    ProcessingCancelledError,
    ProviderExecutionError,
)
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.storage import InMemoryArtifactStore
from sceneforge.media.image import ImageMedia
from sceneforge.runtime.processing_context import ProcessingContext


class FailingProvider:
    """Always raises. Used to test error wrapping and retries."""

    def __init__(self):
        self.calls = 0

    @property
    def name(self) -> str:
        return "failing"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self):
        return frozenset()

    def run(self, media):
        self.calls += 1
        raise RuntimeError("boom")


class FlakyProvider:
    """Fails on the first call, succeeds after that."""

    def __init__(self, fail_times: int = 1):
        self.calls = 0
        self.fail_times = fail_times

    @property
    def name(self) -> str:
        return "flaky"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self):
        return frozenset()

    def run(self, media):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("not yet")
        return [Artifact(kind=ArtifactKind.ARTIFACT, provider=self.name)]


class CountingProvider:
    """Successful provider that counts how many times it actually ran."""

    def __init__(self, name="counting", version="1.0.0"):
        self._name = name
        self._version = version
        self.calls = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def capabilities(self):
        return frozenset()

    def run(self, media):
        self.calls += 1
        return [
            Artifact(kind=ArtifactKind.ARTIFACT, provider=self.name, payload=self.calls)
        ]


def _image():
    return ImageMedia(name="test.jpg", width=10, height=10, fmt="JPEG")


def test_provider_exception_is_wrapped():
    pipeline = Pipeline(provider=FailingProvider())

    with pytest.raises(ProviderExecutionError) as exc_info:
        pipeline.run(_image())

    assert exc_info.value.provider == "failing"
    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_no_retries_by_default():
    provider = FailingProvider()
    pipeline = Pipeline(provider=provider)

    with pytest.raises(ProviderExecutionError):
        pipeline.run(_image())

    assert provider.calls == 1


def test_retries_are_attempted():
    provider = FailingProvider()
    pipeline = Pipeline(provider=provider, max_retries=2, retry_backoff_seconds=0)

    with pytest.raises(ProviderExecutionError):
        pipeline.run(_image())

    assert provider.calls == 3  # 1 initial + 2 retries


def test_retry_recovers_from_transient_failure():
    provider = FlakyProvider(fail_times=1)
    pipeline = Pipeline(provider=provider, max_retries=2, retry_backoff_seconds=0)

    result = pipeline.run(_image())

    assert len(result) == 1
    assert provider.calls == 2


def test_run_detailed_reports_attempts_and_duration():
    provider = FlakyProvider(fail_times=1)
    pipeline = Pipeline(provider=provider, max_retries=2, retry_backoff_seconds=0)

    result = pipeline.run_detailed(_image())

    assert result.attempts == 2
    assert result.duration_seconds >= 0
    assert result.from_cache is False


def test_cancelled_context_raises_before_running():
    provider = CountingProvider()
    pipeline = Pipeline(provider=provider)
    context = ProcessingContext()
    context.cancel()

    with pytest.raises(ProcessingCancelledError):
        pipeline.run(_image(), context=context)

    assert provider.calls == 0


def test_enricher_runs_before_validation():
    class UpperCaseNameEnricher:
        def enrich(self, media):
            return media.evolve(name=media.name.upper())

    seen_names = []

    class RecordingProvider(CountingProvider):
        def run(self, media):
            seen_names.append(media.name)
            return super().run(media)

    pipeline = Pipeline(provider=RecordingProvider(), enricher=UpperCaseNameEnricher())
    pipeline.run(_image())

    assert seen_names == ["TEST.JPG"]


def test_broken_enricher_raises_enrichment_error():
    class BrokenEnricher:
        def enrich(self, media):
            raise ValueError("nope")

    pipeline = Pipeline(provider=CountingProvider(), enricher=BrokenEnricher())

    with pytest.raises(EnrichmentError):
        pipeline.run(_image())


def test_store_caches_successful_results():
    provider = CountingProvider()
    store = InMemoryArtifactStore()
    pipeline = Pipeline(provider=provider, store=store)
    media = _image()

    first = pipeline.run_detailed(media)
    second = pipeline.run_detailed(media)

    assert first.from_cache is False
    assert second.from_cache is True
    assert provider.calls == 1  # second run was served from cache, not re-run
    assert second.artifacts[0].payload == first.artifacts[0].payload


def test_store_cache_is_keyed_by_provider_version():
    store = InMemoryArtifactStore()
    media = _image()

    provider_v1 = CountingProvider(version="1.0.0")
    Pipeline(provider=provider_v1, store=store).run(media)

    provider_v2 = CountingProvider(version="2.0.0")
    result = Pipeline(provider=provider_v2, store=store).run_detailed(media)

    # A version bump must not be served stale results from v1.
    assert result.from_cache is False
    assert provider_v2.calls == 1


def test_failed_run_does_not_populate_cache():
    store = InMemoryArtifactStore()
    provider = FailingProvider()
    pipeline = Pipeline(provider=provider, store=store)
    media = _image()

    with pytest.raises(ProviderExecutionError):
        pipeline.run(media)

    from sceneforge.core.storage import content_key

    key = content_key(media, provider.name, provider.version)
    assert not store.has(key)
