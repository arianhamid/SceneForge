# ADR-0020: Stable API Surface

## Status

Accepted

## Context

SceneForge is reaching the stage where external contributors and
downstream applications need to know which APIs are stable and which
are experimental.

## Decision

### Stable (breaking changes require major version)

- `Media`, `ImageMedia`, `VideoMedia`, `AudioMedia` — immutable domain objects
- `Artifact`, `ArtifactKind`, `ArtifactCategory` — observation vocabulary
- `Provider` (ABC + Protocol) — provider contract
- `Pipeline` — single-provider orchestration
- `Capability` — capability vocabulary
- `PipelineResult` — execution result
- `Registry` — provider discovery

### Experimental (may change without notice)

- `ProcessingContext` — execution internals
- `KnowledgeBuilder`, `RelationshipBuilder` — knowledge layer
- `Entity`, `EntityStore`, `EntityKind` — knowledge persistence
- `Plugin`, `PluginRegistry` — plugin ecosystem
- All contrib providers — may evolve with upstream dependencies
- `AsyncPipeline`, `AsyncProvider` — async execution

### Deliberate Architecture Decisions

- `Pipeline` is a single-provider orchestrator (not multi-provider chain)
- `core/pipeline.py` imports `ProcessingContext` from `runtime` (ADR-backed)
- Knowledge builders import contrib artifact types for isinstance() checks (ADR-0016)
- Providers return `list[Artifact]` — not wrapped in ProviderResult
