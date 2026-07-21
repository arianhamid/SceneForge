# Compatibility Policy

## Stability Levels

### Stable

The following APIs are stable. Breaking changes require major version.

- `Media` (ImageMedia, VideoMedia, AudioMedia)
- `Artifact`
- `Provider` (ABC and Protocol)
- `Pipeline`
- Public exceptions

### Experimental

The following APIs are experimental. Breaking changes may occur.

- Runtime decoders
- Registry internals
- Plugin discovery
- Performance APIs
- Capability registry
- `ArtifactStore` / persistence (`FileArtifactStore`,
  `InMemoryArtifactStore`, `content_key()`) — the serialization format
  in particular is not yet guaranteed stable across versions; don't
  build a production cache on `FileArtifactStore` assuming its on-disk
  JSON shape won't change
- `AsyncProvider` / `AsyncPipeline` — the retry/timeout/concurrency
  parameter shape may still change as real usage surfaces what's
  actually needed
- `MediaEnricher` / `Media.evolve()` — the mechanism is settled (see
  `docs/specifications/PROVIDER_SPEC.md`'s "MediaEnricher" section),
  but only one real enricher (`FFprobeEnricher`) has exercised it so
  far

## What Contributors Can Rely On

- Stable APIs will not break without major version bump
- Experimental APIs may change without notice
- All public APIs are documented
- Tests cover all public behavior

## Python Runtime

SceneForge supports the latest patch release in the Python 3.12 feature series
(`>=3.12,<3.13`). Python 3.11 and 3.13 are outside the supported range. CI,
linting, and type checking use Python 3.12; see
[ADR-0023](adr/0023-python-3-12-baseline.md).

## Versioning

- Major version: Breaking changes to Stable APIs
- Minor version: New features, experimental API changes
- Patch version: Bug fixes, documentation
