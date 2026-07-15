# ADR 0005: Capability Validation

## Status

Accepted

## Context

Providers declare capabilities (e.g., CAPTION, TRANSCRIBE). Should validation happen in providers or Pipeline?

## Decision

Pipeline validates media/compatibility before execution. Providers contain zero capability checks.

## Consequences

- Providers stay simple and focused on computation
- Clear error messages when validation fails
- Single place to add validation logic
- Providers can be tested without worrying about media compatibility

## Alternatives Considered

1. Provider validation — each provider checks its own compatibility
2. No validation — runtime errors when incompatible media is passed
