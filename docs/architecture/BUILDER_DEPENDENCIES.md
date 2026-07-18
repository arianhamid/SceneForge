# Builder Dependency Graph

## Purpose

This document defines the dependency graph and ordering constraints for all knowledge builders in SceneForge.

---

## Dependency Graph

```
FrameExtraction (provider)
        │
        ▼
SceneGroupingBuilder
    Consumes: FrameExtractionArtifact, SceneCutArtifact, TranscriptSegmentArtifact
    Produces: SceneEntity
    Ordering: after frame extraction, after scene detection
        │
        ▼
SceneFaceBuilder
    Consumes: FrameExtractionArtifact, SceneCutArtifact, FaceDetectionArtifact
    Produces: SceneEntity (with face data)
    Ordering: after frame extraction, after scene detection, after face detection
        │
        ▼
SceneMergeBuilder
    Consumes: SceneEntity (from multiple builders)
    Produces: SceneEntity (merged)
    Ordering: after SceneGroupingBuilder, after SceneFaceBuilder
        │
        ▼
SceneSequenceBuilder
    Consumes: SceneEntity
    Produces: RelationshipEntity
    Ordering: after SceneMergeBuilder (or after any SceneEntity producer)
```

---

## Two Builder Shapes

Knowledge Builders operate in two distinct stages (see `docs/architecture/LAYERS.md`):

```
Artifacts -> KnowledgeBuilder.build()      -> Entities   (entity builders)
Entities  -> RelationshipBuilder.relate()  -> Entities   (relationship builders)
```

### Entity Builders

- Consume Artifacts
- Produce Entities
- Never call Providers or Applications
- Never modify the Artifacts they read

### Relationship Builders

- Consume Entities
- Produce Relationship Entities
- Entity representation: `EntityKind.RELATIONSHIP` with `parents` pointing at related entity ids
- No new base type needed — relationships are entities

---

## Rules

1. **Entity builders consume Artifacts, produce Entities.** Never the reverse.

2. **Relationship builders consume Entities, produce Relationships.** Never call Providers.

3. **Never mix entity extraction with relationship inference.** A single builder must be one or the other, not both.

4. **Each builder has a clear, single responsibility.** SceneGroupingBuilder groups frames and transcript segments into scene boundaries. SceneFaceBuilder annotates scenes with face data. SceneMergeBuilder combines partial scene descriptions from multiple builders. SceneSequenceBuilder orders scenes chronologically.

5. **Builders import contrib artifact types for `isinstance()` checks** (ADR-0016). Builders do not import provider modules directly — they depend on artifact types produced by providers, not on the providers themselves.

---

## Builder Details

### SceneGroupingBuilder

Groups `FrameExtractionArtifact` and `TranscriptSegmentArtifact` into the time ranges they overlap, producing one `SceneEntity` per detected scene.

- Consumes: `FrameExtractionArtifact`, `SceneCutArtifact`, `TranscriptSegmentArtifact`
- Produces: `SceneEntity`
- Ordering: after frame extraction, after scene detection

### SceneFaceBuilder

Annotates scenes with face detection data extracted from frames within each scene's time range.

- Consumes: `FrameExtractionArtifact`, `SceneCutArtifact`, `FaceDetectionArtifact`
- Produces: `SceneEntity` (with face data populated)
- Ordering: after frame extraction, after scene detection, after face detection

### SceneMergeBuilder

Combines `SceneEntity` instances produced by different builders for the same scene into a single merged entity. Namespaced by source builder name.

- Consumes: `SceneEntity` (from multiple builders)
- Produces: `SceneEntity` (merged)
- Ordering: after SceneGroupingBuilder, after SceneFaceBuilder

### SceneSequenceBuilder

Links consecutive scenes into a chronological sequence, producing relationship entities.

- Consumes: `SceneEntity`
- Produces: `RelationshipEntity` (with `parents` pointing at scene entity ids)
- Ordering: after SceneMergeBuilder (or after any SceneEntity producer)

---

## Ordering Constraints

Builders must execute in dependency order. A builder cannot begin until all its dependencies have completed:

| Builder | Depends On |
|---------|-----------|
| SceneGroupingBuilder | FrameExtraction (provider), SceneCutArtifact, TranscriptSegmentArtifact |
| SceneFaceBuilder | FrameExtraction (provider), SceneCutArtifact, FaceDetectionArtifact |
| SceneMergeBuilder | SceneGroupingBuilder, SceneFaceBuilder |
| SceneSequenceBuilder | SceneMergeBuilder |

---

## Adding a New Builder

When adding a new builder:

1. **Determine its shape** — does it consume Artifacts (entity builder) or Entities (relationship builder)?

2. **Define its dependencies** — which artifacts or entities does it require?

3. **Document its ordering** — what must complete before it can run?

4. **Keep it focused** — one builder, one responsibility. Split complex transformations into multiple builders with clear interfaces.

5. **Import artifact types from contrib** — never import provider modules directly (ADR-0016).
