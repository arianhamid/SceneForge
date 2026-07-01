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

Every artifact contains:

id

provider

source

created_at

timestamp_start

timestamp_end

metadata

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
