"""
SceneForge Async Pipeline

The synchronous Pipeline forces "one movie's scenes, one at a time."
Real provider calls (Whisper, a VLM, ComfyUI) are I/O/GPU-bound, so a
40-scene movie processed one scene at a time wastes almost all the
wall-clock time waiting. AsyncPipeline is the same Media -> [enrich]
-> validate -> Provider -> Artifacts contract as Pipeline, plus:

  * `run()` supports a deadline (`timeout_seconds`) -- a hung provider
    call doesn't hang the whole run forever
  * `run_many()` processes a batch of Media concurrently, bounded by
    `max_concurrency` so a movie's scenes don't open, say, 40
    simultaneous GPU calls and blow the VRAM budget
  * one item failing in `run_many()` does not cancel the rest of the
    batch -- callers get a `BatchResult` with successes and failures
    separated, matching what actually happens when you process a real
    movie (some scenes fail face-detection, most don't, and a
    single-scene failure shouldn't waste all the others' work)
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from sceneforge.core.artifact import Artifact
from sceneforge.core.async_provider import AsyncProvider
from sceneforge.core.capability_registry import (
    DEFAULT_CAPABILITY_REGISTRY,
    CapabilityRegistry,
)
from sceneforge.core.enrichment import MediaEnricher
from sceneforge.core.exceptions import (
    EnrichmentError,
    IncompatibleMediaError,
    ProviderExecutionError,
    ProviderTimeoutError,
)
from sceneforge.core.pipeline import PipelineResult
from sceneforge.core.storage import ArtifactStore, content_key
from sceneforge.media.base import Media
from sceneforge.runtime.processing_context import ProcessingContext


@dataclass(frozen=True, slots=True)
class BatchResult:
    """Outcome of ``AsyncPipeline.run_many()``: successes and failures, separated."""

    successes: dict[UUID, PipelineResult] = field(default_factory=dict)
    failures: dict[UUID, BaseException] = field(default_factory=dict)

    @property
    def all_succeeded(self) -> bool:
        return not self.failures


class AsyncPipeline:
    """
    Async counterpart to Pipeline, for I/O- and GPU-bound providers.

    Example:
        provider = SyncProviderAdapter(WhisperTranscribeProvider())
        pipeline = AsyncPipeline(provider, timeout_seconds=120, max_concurrency=3)
        batch = await pipeline.run_many(scene_audio_clips)
        for media_id, result in batch.successes.items():
            ...
        for media_id, error in batch.failures.items():
            log.warning("scene %s failed: %s", media_id, error)
    """

    def __init__(
        self,
        provider: AsyncProvider,
        *,
        capability_registry: CapabilityRegistry | None = None,
        enricher: MediaEnricher | None = None,
        store: ArtifactStore | None = None,
        max_retries: int = 0,
        retry_backoff_seconds: float = 0.5,
        timeout_seconds: float | None = None,
        max_concurrency: int = 4,
    ) -> None:
        self._provider = provider
        self._capability_registry = capability_registry or DEFAULT_CAPABILITY_REGISTRY
        self._enricher = enricher
        self._store = store
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds
        self._timeout_seconds = timeout_seconds
        self._max_concurrency = max(1, max_concurrency)

    @property
    def provider(self) -> AsyncProvider:
        return self._provider

    def _validate_media(self, media: Media) -> None:
        capabilities = self._provider.capabilities
        if not capabilities:
            return
        media_type = type(media)
        for capability in capabilities:
            if not self._capability_registry.is_compatible(capability, media_type):
                raise IncompatibleMediaError(
                    provider=self._provider.name,
                    media_type=media_type.__name__,
                    capabilities={cap.value for cap in capabilities},
                )

    async def _enrich(self, media: Media) -> Media:
        if self._enricher is None:
            return media
        try:
            result = self._enricher.enrich(media)
            if asyncio.iscoroutine(result):
                result = await result
            return result
        except Exception as exc:  # noqa: BLE001 - re-branded below
            raise EnrichmentError(type(self._enricher).__name__, exc) from exc

    async def run(
        self,
        media: Media,
        context: ProcessingContext | None = None,
    ) -> list[Artifact[Any]]:
        """Process media through the provider and return artifacts."""
        result = await self.run_detailed(media, context=context)
        return result.artifacts

    async def run_detailed(
        self,
        media: Media,
        context: ProcessingContext | None = None,
    ) -> PipelineResult:
        """Like ``run()``, but returns timing/retry/cache/enriched-media detail too."""
        context = context if context is not None else ProcessingContext()
        context.ensure_running()

        media = await self._enrich(media)
        self._validate_media(media)

        cache_key: str | None = None
        if self._store is not None:
            cache_key = content_key(media, self._provider.name, self._provider.version)
            cached = self._store.get(cache_key)
            if cached is not None:
                return PipelineResult(
                    artifacts=cached,
                    media=media,
                    duration_seconds=0.0,
                    attempts=0,
                    from_cache=True,
                )

        max_attempts = self._max_retries + 1
        attempt = 0
        last_error: BaseException | None = None
        start = time.monotonic()

        while attempt < max_attempts:
            attempt += 1
            context.ensure_running()
            try:
                if self._timeout_seconds is not None:
                    artifacts = list(
                        await asyncio.wait_for(
                            self._provider.run(media), timeout=self._timeout_seconds
                        )
                    )
                else:
                    artifacts = list(await self._provider.run(media))
            except TimeoutError as exc:
                last_error = ProviderTimeoutError(
                    self._provider.name, self._timeout_seconds or 0.0
                )
                last_error.__cause__ = exc
                if attempt < max_attempts:
                    await asyncio.sleep(self._retry_backoff_seconds * attempt)
                continue
            except Exception as exc:  # noqa: BLE001 - provider is third-party code
                last_error = exc
                if attempt < max_attempts:
                    await asyncio.sleep(self._retry_backoff_seconds * attempt)
                continue
            else:
                duration = time.monotonic() - start
                if self._store is not None and cache_key is not None:
                    self._store.put(cache_key, artifacts)
                return PipelineResult(
                    artifacts=artifacts,
                    media=media,
                    duration_seconds=duration,
                    attempts=attempt,
                    from_cache=False,
                )

        assert last_error is not None  # loop only exits here via the except branch
        if isinstance(last_error, ProviderTimeoutError):
            raise last_error
        raise ProviderExecutionError(self._provider.name, last_error) from last_error

    async def run_many(
        self,
        media_items: list[Media],
        context: ProcessingContext | None = None,
    ) -> BatchResult:
        """
        Process many Media items concurrently, bounded by ``max_concurrency``.

        One item failing (including timing out, after retries) does
        not cancel the rest of the batch -- it's recorded in
        ``BatchResult.failures`` keyed by ``media.id`` while every
        other item keeps running.
        """
        context = context if context is not None else ProcessingContext()
        semaphore = asyncio.Semaphore(self._max_concurrency)
        successes: dict[UUID, PipelineResult] = {}
        failures: dict[UUID, BaseException] = {}

        async def _bounded_run(item: Media) -> None:
            async with semaphore:
                try:
                    result = await self.run_detailed(item, context=context)
                except Exception as exc:  # noqa: BLE001 - isolate this item's failure
                    failures[item.id] = exc
                else:
                    successes[item.id] = result

        await asyncio.gather(*(_bounded_run(item) for item in media_items))
        return BatchResult(successes=successes, failures=failures)
