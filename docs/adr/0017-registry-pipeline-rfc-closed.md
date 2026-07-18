# ADR 0017: Registry/Pipeline Wiring Is Closed as Unnecessary, Not Implemented

## Status

Accepted

## Context

`docs/specifications/REGISTRY_SPEC.md`'s "Known gap" — `Registry`
(provider lookup by name/capability) and `Pipeline` (single-provider
orchestration) have never been connected — has appeared in
`.ai/PROJECT_STATE.md`'s open RFCs every sprint since Sprint 3, each
time deferred as "not blocking yet." `.ai/NEXT_TASK.md` required
Sprint 9 to either implement the wiring or close the RFC explicitly,
rather than deferring a seventh time by default.

## Decision

**Closed as unnecessary, not implemented.** Six sprints of building
real providers, real Knowledge Builders, and real examples never
produced a single real caller that needed to select a provider by
capability at runtime rather than importing and constructing it
directly. Every real usage in this codebase —
`examples/end_to_end/analyze_video.py`, every integration test, every
Provider Spec example — constructs its provider explicitly:
`Pipeline(provider=FFmpegFrameExtractionProvider(...))`, not
`Pipeline(provider=registry.by_capability(Capability.FRAME_EXTRACTION)[0])`.

Per `docs/philosophy/VISION.md` principle 7 ("prove it before you
formalize it"), six sprints without a real need is itself the answer:
building the wiring now would be speculative infrastructure for a use
case that has never actually shown up, the same mistake every other
ADR in this series has avoided by waiting for real evidence first.

`Registry` remains available and functional
(`docs/specifications/REGISTRY_SPEC.md`, demonstrated in
`examples/core/registry_basic.py`) for callers who *do* want to
register providers and query by capability manually — nothing is
removed. What's closed is only the open question of whether `Pipeline`
itself should grow a way to accept a `Registry` and select a provider
automatically.

## Consequences

- `.ai/PROJECT_STATE.md`'s Open RFCs section no longer carries this
  item forward. If a real need for runtime provider selection appears
  in a future sprint (e.g. a CLI accepting `--capability
  frame_extraction` and needing to pick among several registered
  providers), that's new evidence and reopens the question — this ADR
  documents that the answer was "not yet" as of Sprint 9, not "never."
- No code changes accompany this ADR. That's the point: the decision
  itself is the artifact.

## Alternatives Considered

1. **Implement the wiring anyway**, since it was "eventually going to
   be needed." Rejected — "eventually" is not evidence, and every
   other structural decision in this project (ADR-0011 through 0016)
   was made only once a real need existed, not preemptively. This ADR
   applies that same discipline to a case where the honest answer is
   "no real need has appeared," not just "the need was smaller than
   expected."
2. **Silently drop the RFC without recording a decision**, letting it
   quietly disappear from `.ai/PROJECT_STATE.md`. Rejected: a future
   sprint (or a future AI session working on this codebase) deserves
   to know this was actively decided, not merely forgotten — the same
   reasoning behind writing an ADR at all instead of just fixing code
   silently.
