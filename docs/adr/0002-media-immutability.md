# ADR 0002: Media Immutability

## Status

Accepted

## Context

Media objects represent source files (images, videos, audio). We need to decide if they should be mutable or immutable.

## Decision

Media objects are immutable after construction. Use `frozen=True` and `slots=True` on all dataclasses.

## Consequences

- No accidental mutation of media objects
- Safe to share across providers and pipelines
- Clear lifetime semantics
- Metadata wrapped in MappingProxyType for true immutability

## Alternatives Considered

1. Mutable — simpler but error-prone
2. Copy-on-write — complex, unnecessary for this use case
