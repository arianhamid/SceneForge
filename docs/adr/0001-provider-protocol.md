# ADR 0001: Provider Protocol

## Status

Accepted

## Context

SceneForge needs a way to define providers that process media into artifacts. We need to decide between ABC inheritance and structural typing (Protocol).

## Decision

Use both: ABC for explicit inheritance, Protocol for structural typing. Pipeline uses Protocol, providers can use either.

## Consequences

- Providers can be implemented without inheriting from ABC
- Pipeline works with any object that has a `run()` method
- ABC provides clear documentation of required interface
- Protocol enables duck typing and easier testing

## Alternatives Considered

1. ABC only — more explicit but less flexible
2. Protocol only — less documentation, harder to discover interface
