# ADR 0004: Runtime Representations

## Status

Accepted

## Context

Providers need decoded media data (pixels, audio samples). Should decoded data be part of Media or separate?

## Decision

Decoded representations are execution-time objects in the runtime layer. Media stays immutable and represents identity only.

## Consequences

- Clean separation between identity (Media) and state (Representation)
- Different lifetimes: Media lives forever, Representations are ephemeral
- Easy to swap decoding backends (NumPy, Torch, GPU)
- Memory management is clearer

## Alternatives Considered

1. DecodedMedia as domain objects — mixes identity and state
2. Providers decode directly — duplicates decoding logic
