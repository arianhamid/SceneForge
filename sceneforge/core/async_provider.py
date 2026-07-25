"""
SceneForge Async Provider

Real AI providers (Whisper transcription, a VLM captioner, a ComfyUI
render call) are I/O- or GPU-bound and slow -- seconds to minutes per
call. The synchronous Provider protocol forces a caller processing a
movie's 40 scenes to run every provider call one at a time.
AsyncProvider is the same contract, just awaitable, so an
AsyncPipeline can run many calls concurrently (bounded by a
semaphore, not by however the OS happens to schedule things).

A synchronous Provider can always be adapted into an AsyncProvider
with `SyncProviderAdapter` -- there's no need to write two
implementations of the same provider.
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol, runtime_checkable

from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.provider_protocol import Provider
from sceneforge.media.base import Media


@runtime_checkable
class AsyncProvider(Protocol):
    """Protocol for processing media into artifacts asynchronously."""

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def capabilities(self) -> frozenset[Capability]: ...

    @property
    def execution_fingerprint(self) -> str:
        """Folded into `content_key()` (ADR-0024 Phase 0 item 2)."""
        ...

    async def run(self, media: Media) -> list[Artifact[Any]]:
        """Process media and return artifacts."""
        ...


class SyncProviderAdapter:
    """
    Wraps a synchronous Provider so it satisfies AsyncProvider.

    Runs the synchronous `run()` in the event loop's shared executor so a slow,
    blocking, GPU-bound call doesn't stall the event loop -- and therefore
    doesn't stall every other concurrent scene's provider call in the same
    `AsyncPipeline.run_many()` batch. Reusing the executor avoids creating a new
    operating-system thread for every call.
    """

    def __init__(self, provider: Provider) -> None:
        self._provider = provider

    @property
    def name(self) -> str:
        return self._provider.name

    @property
    def version(self) -> str:
        return self._provider.version

    @property
    def capabilities(self) -> frozenset[Capability]:
        return self._provider.capabilities

    @property
    def execution_fingerprint(self) -> str:
        return self._provider.execution_fingerprint

    async def run(self, media: Media) -> list[Artifact[Any]]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._provider.run, media)
