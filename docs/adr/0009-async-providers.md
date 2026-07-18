# ADR 0009: AsyncProvider and AsyncPipeline Exist Alongside the Sync Versions

## Status

Accepted

## Context

Real Providers (an STT model, a captioning VLM, a ComfyUI render call)
are I/O- or GPU-bound and slow — seconds to minutes per call. The
synchronous `Provider`/`Pipeline` contract forces a caller processing
a movie's scenes to run every provider call one at a time, which is
the actual bottleneck reported in real usage of this pattern
(per-scene stage pipelines with GPU-bound calls). `Pipeline` also had
no timeout, so a hung provider call hung the whole run indefinitely,
and no facility for "some scenes fail, most don't" — a single
exception aborted an entire batch.

## Decision

`AsyncProvider` (`sceneforge/core/async_provider.py`) is the same
`name`/`version`/`capabilities`/`run()` contract as `Provider`, with
`run()` declared `async`. `SyncProviderAdapter` wraps any synchronous
`Provider` to satisfy `AsyncProvider` by running it in the default
executor thread pool, so existing/simple providers don't need a
duplicate async implementation.

`AsyncPipeline` (`sceneforge/core/async_pipeline.py`) mirrors
`Pipeline`'s `run()`/`run_detailed()` contract (enrichment → capability
validation → cache lookup → provider call → cache write), plus:

- `timeout_seconds`: wraps the provider call in `asyncio.wait_for()`;
  a timeout raises `ProviderTimeoutError` after retries are exhausted,
  the same way a raised exception raises `ProviderExecutionError`.
- `run_many(media_items)`: processes a batch concurrently, bounded by
  `max_concurrency` (an `asyncio.Semaphore`) so a movie's scenes don't
  open unbounded simultaneous GPU calls. Returns a `BatchResult` with
  `successes`/`failures` dicts keyed by `media.id` — one item failing
  does not cancel the batch.

## Consequences

- A real transcription/captioning provider can be written once, as an
  `AsyncProvider`, and processed at whatever concurrency the caller's
  hardware (VRAM, API rate limits) actually supports, instead of
  serially.
- `Pipeline` (sync) is unchanged and still the right choice for
  single-item, script-style usage — `AsyncPipeline` isn't a
  replacement, it's the tool for batches of slow calls.
- `BatchResult.failures` makes partial failure a first-class, typed
  outcome instead of an exception a caller has to wrap `run_many` in
  a broad `try/except` to approximate.
- Two parallel implementations (`Pipeline`/`AsyncPipeline`) mean two
  places to keep behavior consistent (cache-key derivation, retry
  backoff shape, error wrapping). Accepted as the cost of not forcing
  every synchronous caller into `asyncio` — revisit if the duplication
  causes a real bug from drift between the two.

## Alternatives Considered

1. Make `Pipeline` async-only and have synchronous callers wrap it in
   `asyncio.run()` — rejected: forces every simple script-style use
   case (the majority of usage so far) to deal with an event loop for
   no benefit.
2. Use threads instead of `asyncio` for concurrency — rejected for I/O-
   bound model API calls (asyncio is the more natural fit and
   composes with `asyncio.wait_for`/`asyncio.Semaphore` cleanly); for
   CPU/GPU-bound synchronous libraries, `SyncProviderAdapter`'s
   executor-thread wrapping already gets the benefit of threads
   without forcing every provider author to choose.
