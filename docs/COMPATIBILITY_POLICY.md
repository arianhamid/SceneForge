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

## What Contributors Can Rely On

- Stable APIs will not break without major version bump
- Experimental APIs may change without notice
- All public APIs are documented
- Tests cover all public behavior

## Versioning

- Major version: Breaking changes to Stable APIs
- Minor version: New features, experimental API changes
- Patch version: Bug fixes, documentation
