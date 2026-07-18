# Artifact Specification

## Purpose

Artifacts are immutable observations extracted directly from source media.

Artifacts represent facts.

They never contain assumptions or reasoning.

---

# Characteristics

Every artifact must satisfy the following properties.

## Immutable

Once created, an artifact never changes.

Corrections create new artifacts.

---

## Serializable

Artifacts can be written to disk without information loss.

---

## Timestamped

Artifacts always know when they occurred.

---

## Traceable

Artifacts know which provider produced them.

---

## Reproducible

Running the same provider on the same input should produce an equivalent artifact.

---

# Required Fields

This section previously listed `source`, `timestamp_start`, and
`timestamp_end` as required fields — none of those exist on the actual
`Artifact` dataclass and never did. Documenting fields that don't exist
is worse than documenting none; this is the corrected list, matching
`sceneforge/core/artifact.py` exactly:

- `id` — UUID, auto-generated
- `kind` — an `ArtifactKind` (prevents string-typo'd artifact types)
- `provider` — the name of the provider that produced this artifact
- `created_at` — UTC timestamp of creation
- `payload` — the actual observation (`Artifact[str]` for a caption,
  `Artifact[None]` for a marker-only artifact like `IdentityArtifact`)
- `metadata` — provider-specific extra data, wrapped `MappingProxyType`
  at construction (truly immutable, not just conventionally so)
- `parents` — tuple of UUIDs; how a correction/derived artifact links
  back to the artifact(s) it was built from, without mutating them

A specific artifact type (e.g. `FrameExtractionArtifact` in
`sceneforge.contrib.ffmpeg`) adds its own fields as dataclass
subclassing — `media_id`, `frame_path`, `timestamp_seconds`, etc.
There is no single fixed schema every artifact type must match beyond
the base fields above; per-kind fields belong to the subclass, not to
this base spec.

---

# Persistence

"Serializable" above is now a testable property, not just an intent:
`sceneforge.core.storage.artifact_to_dict()` / `artifact_from_dict()`
round-trip any `Artifact` subclass generically via `dataclasses.fields()`.
Exact-type round-tripping (getting your subclass back, not the generic
base `Artifact`) requires registering it once:

```python
from sceneforge.core.storage import register_artifact_type

@register_artifact_type
@dataclass(frozen=True, slots=True)
class MyArtifact(Artifact[str]):
    confidence: float = 0.0
```

Every artifact type shipped in `sceneforge.contrib` already does this.
See `docs/adr/0008-artifact-persistence.md`.

---

# Metadata

Metadata is provider-specific.

Examples

confidence

model_version

processing_time

resolution

language

etc.

The framework never interprets provider metadata.

---

# Examples

Frame

Transcript Segment

Scene Cut

OCR Block

Caption

Embedding

Face Detection

Object Detection

Audio Chunk

---

# Forbidden

Artifacts must never contain:

Reasoning

Character identity

Story summaries

Relationships

Themes

Predictions

Those belong to higher layers.
