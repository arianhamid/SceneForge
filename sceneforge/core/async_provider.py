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
import threading
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

    async def run(self, media: Media) -> list[Artifact[Any]]:
        """Process media and return artifacts."""
        ...


class SyncProviderAdapter:
    """
    Wraps a synchronous Provider so it satisfies AsyncProvider.

    Runs the synchronous `run()` in a worker thread so a slow, blocking,
    GPU-bound call doesn't stall the event loop -- and therefore doesn't stall
    every other concurrent scene's provider call in the same
    `AsyncPipeline.run_many()` batch.

    Completion is signaled with a `threading.Event` rather than an executor
    future callback. Constrained runtimes can lose that callback's selector
    wake-up even though the worker has finished, leaving the coroutine hung.
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

    async def run(self, media: Media) -> list[Artifact[Any]]:
        completed = threading.Event()
        result: list[list[Artifact[Any]]] = []
        errors: list[BaseException] = []

        def _run_provider() -> None:
            try:
                result.append(self._provider.run(media))
            except BaseException as exc:
                errors.append(exc)
            finally:
                completed.set()

        worker = threading.Thread(
            target=_run_provider,
            name=f"sceneforge-{self._provider.name}",
        )
        worker.start()

        while not completed.is_set():
            await asyncio.sleep(0.01)

        worker.join()
        if errors:
            raise errors[0]
        return result[0]
