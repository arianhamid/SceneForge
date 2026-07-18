# ADR 0003: Pipeline Orchestration

## Status

Accepted

## Context

We need a single entry point for processing media through providers. Should Pipeline be a thin wrapper or own orchestration logic?

## Decision

Pipeline is the orchestration boundary. It owns: capability validation, timing, errors, composition. Providers own computation only.

## Consequences

- Clear separation of concerns
- Pipeline can add cross-cutting concerns without changing providers
- Providers remain simple and focused
- Easy to add logging, metrics, retries at Pipeline level

## Alternatives Considered

1. Provider chains — providers would need to manage orchestration
2. No Pipeline — users would write orchestration manually

## Update (Genesis Sprint 2)

The original implementation only fulfilled half of this decision:
`Pipeline` validated capabilities but never actually timed execution,
wrapped provider errors, or threaded the (already-existing but unused)
`ProcessingContext` through a run. "Owns timing, errors, composition"
was aspirational, not implemented. `Pipeline.run_detailed()` now does
all three (see `PipelineResult`), plus retries and optional
`ArtifactStore` caching — see ADR-0007 and ADR-0008 for the pieces
that made this possible without reintroducing global state.
