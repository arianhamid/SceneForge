# ADR 0006: Provider Protocol Must Declare Its Full Structural Contract

## Status

Accepted

## Context

`sceneforge.core.provider_protocol.Provider` (the structural,
duck-typed contract, as opposed to `sceneforge.core.provider.Provider`,
the ABC) declared only `run()`. But `Pipeline._validate_media()` reads
`self._provider.capabilities`, and error paths read
`self._provider.name` — attributes the Protocol never claimed a
conforming object had. A class satisfying the documented Protocol
(only `run()`) would crash the instant `Pipeline` touched
`.capabilities`. `mypy --strict` didn't catch this because nothing had
type-checked `Pipeline` against a value actually typed as the
Protocol until this pass.

## Decision

`provider_protocol.Provider` declares `name`, `version`,
`capabilities`, and `run()` — the same four members the ABC `Provider`
requires. A structural provider (one that doesn't inherit from the
ABC) must implement all four to satisfy the Protocol; `isinstance()`
checks against it now correctly reject `run()`-only classes.

## Consequences

- `mypy --strict` now catches a `Pipeline` (or `AsyncPipeline`, or any
  new code) that assumes an attribute the Protocol doesn't guarantee.
- A previously-passing test (`test_runtime_checkable`) that asserted a
  `run()`-only class satisfied `Provider` was itself encoding the bug;
  it's replaced with two tests — one showing the complete contract
  passes, one showing a partial contract correctly fails.
- Third-party structural providers that only implemented `run()`
  (relying on the old, incomplete Protocol) will need `name`,
  `version`, and `capabilities` added. Given the framework has no
  external consumers yet, the cost of tightening this now is as close
  to zero as it will ever be.

## Alternatives Considered

1. Leave the Protocol as `run()`-only and have `Pipeline` use
   `getattr(provider, "capabilities", frozenset())` defensively —
   rejected: this hides a real contract violation behind a silent
   default instead of surfacing it at the type-checking or
   `isinstance()` boundary where it belongs.
2. Merge the ABC and Protocol into a single type — rejected for now;
   the split serves a real purpose (ADR-0001), and the fix here is
   narrower: make the Protocol accurately describe what `Pipeline`
   actually needs, not remove the distinction.
