# ADR 0008: ArtifactStore Is a First-Class, Injectable Persistence Layer

## Status

Accepted

## Context

`docs/philosophy/VISION.md`'s north star is "a movie is analyzed once,
its understanding becomes reusable forever." Before this pass, nothing
in the framework persisted anything — every `Pipeline.run()` call
produced fresh `Artifact` objects that lived only as long as the
Python process holding them. Nothing distinguished "we already ran
this provider on this file" from "we've never touched this file",
which made the north star aspirational rather than testable.

## Decision

`ArtifactStore` is a `Protocol` (`sceneforge/core/storage.py`) —
`put`/`get`/`has`/`delete`, keyed by a string. `content_key(media,
provider_name, provider_version)` derives that key deterministically
from media identity plus provider name and version, so:

- re-running the same provider against the same media is a cache
  lookup, not a re-run;
- upgrading a provider (a real model swap) naturally invalidates the
  cache, because the version is part of the key, rather than silently
  serving stale results.

`Pipeline` and `AsyncPipeline` take an optional `store:
ArtifactStore | None`. When set, `run_detailed()` checks the store
before calling the provider and writes the result after a successful
run; a failed run never populates the cache. Two implementations ship:
`FileArtifactStore` (one JSON file per key, survives process restarts)
and `InMemoryArtifactStore` (for tests and short scripts).

Artifacts serialize via `artifact_to_dict()`/`artifact_from_dict()`,
which use `dataclasses.fields()` generically rather than hardcoding
`Artifact`'s known fields, so any dataclass subclass round-trips.
Exact-type round-tripping (getting a `FrameExtractionArtifact` back
instead of the generic `Artifact` base class) requires opting in via
`@register_artifact_type` — every artifact type shipped in
`sceneforge.contrib` does this already.

## Consequences

- "Analyze once, reuse forever" is now a property you can write a test
  for (`test_store_caches_successful_results`,
  `test_pipeline_caches_frame_extraction_results`), not just a claim
  in a markdown file.
- `FileArtifactStore` is explicitly *not* a production database — it's
  the smallest thing that makes the promise real today. A real backend
  (SQLite, an embedded graph DB, object storage) is an open question
  in `.ai/PROJECT_STATE.md`, deferred until there's enough real
  artifact data to know what queries actually matter.
- Cache correctness now depends on `provider.version` actually
  changing when provider behavior changes. This is a discipline
  requirement on every future Provider author, not something the
  framework can enforce mechanically — worth calling out explicitly in
  `PROVIDER_SPEC.md`.
- `content_key()` is derived from `media.id`, which `Media.evolve()`
  preserves. An enriched `Media` and its placeholder predecessor share
  an identity, so caching keys off the *post-enrichment* media (which
  is what `Pipeline` does — enrichment runs before the cache lookup).
  Flagged as an open RFC in `.ai/PROJECT_STATE.md` pending a second
  real provider to confirm this is the right call in practice.

## Alternatives Considered

1. Key the cache off a hash of file bytes instead of `media.id` —
   more robust against duplicate files with different `Media`
   identities, but requires reading the whole file (expensive for
   large video) just to check a cache. Deferred; can be layered in via
   a different `content_key()` implementation later without changing
   the `ArtifactStore` protocol.
2. Build straight to a SQLite-backed store — rejected for this pass
   per "prove it before you formalize it" (`docs/philosophy/VISION.md`
   principle 7): the Protocol boundary matters more right now than the
   backend behind it.
