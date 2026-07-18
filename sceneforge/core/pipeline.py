"""
SceneForge Pipeline

The synchronous orchestration boundary for SceneForge: Media -> [enrich]
-> validate -> Provider -> Artifacts.

Historically this module also held a module-level, mutable
`_CAPABILITY_MEDIA_MAP` dict plus a `Pipeline._capabilities_registered`
class flag used to fake one-time global init. That was hidden shared
state that violated the framework's own "no hidden state" principle
and made two Pipelines in one process (e.g. in tests) able to
interfere with each other. Capability data now lives in an injectable
`CapabilityRegistry` (see `capability_registry.py`).

Pipeline also used to silently let any provider exception escape
unwrapped and never touched `ProcessingContext` at all, despite
ADR-0003 claiming Pipeline "owns timing, errors, composition." It now
actually does:
  * threads a `ProcessingContext` through the run (creating a default
    one if the caller doesn't supply it) and checks for cancellation
    before *and* between attempts
  * times the provider call and records it on the context
  * optionally retries a failing provider with linear backoff
  * wraps provider exceptions in `ProviderExecutionError` (with the
    original exception preserved as `__cause__`) instead of letting
    arbitrary third-party exceptions escape unbranded
  * optionally runs a `MediaEnricher` first, so Media with placeholder
    metadata (e.g. a freshly-loaded VideoMedia with `fps=0.0`) can be
    turned into authoritative Media before the provider ever sees it
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from sceneforge.core.artifact import Artifact
from sceneforge.core.capability_registry import (
    DEFAULT_CAPABILITY_REGISTRY,
    CapabilityRegistry,
)
from sceneforge.core.enrichment import MediaEnricher
from sceneforge.core.exceptions import (
    EnrichmentError,
    IncompatibleMediaError,
    ProviderExecutionError,
)
from sceneforge.core.provider_protocol import Provider
from sceneforge.core.storage import ArtifactStore, content_key
from sceneforge.media.base import Media
from sceneforge.runtime.processing_context import ProcessingContext


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """
    The full outcome of a Pipeline run, not just the artifact list.

    `Pipeline.run()` stays backward compatible by returning a plain
    `list[Artifact]`; `Pipeline.run_detailed()` is the entry point for
    callers who also want timing, retry count, cache status, and the
    (possibly enriched) Media that was actually validated and
    processed.
    """

    artifacts: list[Artifact[Any]]
    media: Media
    duration_seconds: float
    attempts: int
    from_cache: bool = False


class Pipeline:
    """
    The orchestration boundary for SceneForge.

    Pipeline is the single entry point for processing media through a
    provider. It owns the workflow: Media -> [enrich] -> validate ->
    Provider -> Artifacts, plus timing, retries, cancellation, and
    error wrapping around that workflow.

    Example:
        pipeline = Pipeline(provider=IdentityProvider())
        artifacts = pipeline.run(media)

        # With retries and a shared registry across many pipelines:
        registry = CapabilityRegistry()
        registry.register(Capability.CAPTION, {ImageMedia})
        pipeline = Pipeline(
            provider=CaptionProvider(),
            capability_registry=registry,
            max_retries=2,
        )
    """

    def __init__(
        self,
        provider: Provider,
        *,
        capability_registry: CapabilityRegistry | None = None,
        enricher: MediaEnricher | None = None,
        store: ArtifactStore | None = None,
        max_retries: int = 0,
        retry_backoff_seconds: float = 0.5,
    ) -> None:
        """
        Initialize Pipeline.

        Args:
            provider: The provider to use for processing.
            capability_registry: Which media types each capability
                supports. Defaults to a shared, pre-populated registry
                covering SceneForge's built-in capabilities. Pass your
                own instance to isolate a pipeline (tests, plugins
                with custom capabilities) from that shared default.
            enricher: Optional MediaEnricher run before validation, so
                placeholder Media (e.g. from a cheap filesystem-only
                loader) can be turned into authoritative Media first.
            store: Optional ArtifactStore. When set, ``run()``/
                ``run_detailed()`` look up a cached result keyed on
                media identity + provider name + provider version
                before calling the provider, and persist a fresh
                result after a successful run. This is what makes
                "analyze once, reuse forever" literally true rather
                than aspirational.
            max_retries: Number of *additional* attempts after the
                first if the provider raises. 0 (default) means no
                retries -- a failure is wrapped and raised immediately.
            retry_backoff_seconds: Linear backoff multiplier between
                retries (attempt N sleeps ``retry_backoff_seconds * N``).
        """
        self._provider = provider
        self._capability_registry = capability_registry or DEFAULT_CAPABILITY_REGISTRY
        self._enricher = enricher
        self._store = store
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds

    @property
    def provider(self) -> Provider:
        return self._provider

    def _validate_media(self, media: Media) -> None:
        """
        Validate that media is compatible with provider capabilities.

        Raises:
            IncompatibleMediaError: If media is incompatible with
                capabilities.
        """
        capabilities = self._provider.capabilities

        # If provider has no capabilities, accept all media.
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

    def _enrich(self, media: Media) -> Media:
        if self._enricher is None:
            return media
        try:
            return self._enricher.enrich(media)
        except Exception as exc:  # noqa: BLE001 - re-branded below, not swallowed
            enricher_name = type(self._enricher).__name__
            raise EnrichmentError(enricher_name, exc) from exc

    def run(
        self,
        media: Media,
        context: ProcessingContext | None = None,
    ) -> list[Artifact[Any]]:
        """
        Process media through the provider and return artifacts.

        Args:
            media: The media object to process.
            context: Optional ProcessingContext for cancellation and
                shared run metadata. A fresh one is created if omitted.

        Returns:
            A list of artifacts produced by the provider.

        Raises:
            IncompatibleMediaError: If media is incompatible with
                capabilities.
            EnrichmentError: If the configured enricher fails.
            ProviderExecutionError: If the provider raises and retries
                (if any) are exhausted.
            ProcessingCancelledError: If ``context`` was cancelled
                before or during the run.
        """
        return self.run_detailed(media, context=context).artifacts

    def run_detailed(
        self,
        media: Media,
        context: ProcessingContext | None = None,
    ) -> PipelineResult:
        """Like ``run()``, but returns timing/retry/cache/enriched-media detail too."""
        context = context if context is not None else ProcessingContext()
        context.ensure_running()

        media = self._enrich(media)
        self._validate_media(media)

        cache_key: str | None = None
        if self._store is not None:
            cache_key = content_key(media, self._provider.name, self._provider.version)
            cached = self._store.get(cache_key)
            if cached is not None:
                context.metadata[f"{self._provider.name}.cache_hit"] = True
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
                artifacts = list(self._provider.run(media))
            except Exception as exc:  # noqa: BLE001 - provider is third-party code
                last_error = exc
                if attempt < max_attempts:
                    time.sleep(self._retry_backoff_seconds * attempt)
                continue
            else:
                duration = time.monotonic() - start
                context.metadata[f"{self._provider.name}.duration_seconds"] = duration
                context.metadata[f"{self._provider.name}.attempts"] = attempt
                if self._store is not None and cache_key is not None:
                    self._store.put(cache_key, artifacts)
                return PipelineResult(
                    artifacts=artifacts,
                    media=media,
                    duration_seconds=duration,
                    attempts=attempt,
                    from_cache=False,
                )

        duration = time.monotonic() - start
        context.metadata[f"{self._provider.name}.duration_seconds"] = duration
        context.metadata[f"{self._provider.name}.attempts"] = attempt
        assert last_error is not None  # loop only exits here via the except branch
        raise ProviderExecutionError(self._provider.name, last_error) from last_error
