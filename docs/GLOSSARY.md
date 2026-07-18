Artifact

Observation extracted from media by a Provider. Immutable, serializable.

ArtifactStore

Content-addressable persistence for Artifacts, keyed by media identity
+ provider name + version. What makes "analyze once, reuse forever" a
literal, cacheable property instead of an aspiration.

Media

The source object a Provider operates on (ImageMedia, VideoMedia,
AudioMedia). Immutable; corrected via `evolve()`, never mutated.

MediaEnricher

Turns placeholder Media metadata (from a cheap, filesystem-only
loader) into authoritative metadata, by returning a new Media instance
via `evolve()`. Runs before a Provider sees the Media.

Capability

A named framework feature (`CAPTION`, `TRANSCRIBE`, `DETECT_SCENES`,
...) that code depends on instead of a specific model or library.

Knowledge

Facts derived from multiple artifacts.

Reasoning

Relationships inferred from knowledge.

Application

A consumer of knowledge.

Provider

A producer of artifacts. Implements one or more capabilities.

Pipeline

An orchestrator for one Provider's execution against one Media object:
enrich, validate, check cache, run, populate cache. Not (yet) a
multi-provider chain — see `docs/architecture/DOMAIN_MODEL.md`.

Plugin

A package extending the framework, discoverable via
`importlib.metadata.entry_points()`.
