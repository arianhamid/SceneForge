# ADR 0007: Capability Data Lives in an Injectable Registry, Not Global State

## Status

Accepted

## Context

Capability-to-media-type mappings lived in a module-level mutable
dict, `sceneforge.core.pipeline._CAPABILITY_MEDIA_MAP`, populated by a
side-effecting `register_default_capabilities()` function guarded by a
`Pipeline._capabilities_registered` class-level flag meant to fake
one-time initialization. Two `Pipeline` instances in the same process
shared this dict whether they wanted to or not — registering a custom
capability mapping for one pipeline (e.g. in a test, or a plugin with
non-default media-type support) silently affected every other pipeline
in the same interpreter. This directly contradicts
`docs/philosophy/VISION.md`'s "no hidden state" principle, and was
exactly the kind of bug that's invisible until two tests run in an
order that happens to interact.

## Decision

Capability data lives in a plain `CapabilityRegistry` object
(`sceneforge/core/capability_registry.py`). `Pipeline` (and
`AsyncPipeline`) take one via constructor injection, defaulting to a
shared, pre-populated `DEFAULT_CAPABILITY_REGISTRY` for convenience.
Anyone who needs isolation — tests, a plugin registering non-default
capabilities, two independent pipelines in one process with different
rules — constructs their own `CapabilityRegistry()` and passes it
explicitly.

## Consequences

- Two `Pipeline`s can now genuinely coexist with different capability
  rules in the same process without interference (see
  `test_two_registries_are_isolated`).
- `Pipeline.__init__` no longer has a "first pipeline built in this
  process pays an init tax" side effect — construction is a pure,
  predictable operation.
- Callers who don't care about isolation pay no cost: the default
  registry is built once at import time and reused, same as before.
- `register_capability_media()` and `register_default_capabilities()`
  no longer exist. There is no known external caller (framework has no
  release yet), so this is a clean break rather than a deprecation.

## Alternatives Considered

1. Keep the global dict but make it thread-local — rejected: solves
   thread-safety, not the actual problem, which is *any* two
   `Pipeline`s sharing capability rules by default regardless of
   threading.
2. Make `CapabilityRegistry` a singleton with an explicit `.reset()`
   for tests — rejected: still hidden global state, just with an
   escape hatch; the escape hatch itself becomes a footgun (forgetting
   to call `.reset()` between tests).
