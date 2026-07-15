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
