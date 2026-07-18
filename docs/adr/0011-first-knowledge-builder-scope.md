# ADR 0011: The First Knowledge Builder Groups by Time Overlap Only

## Status

Accepted

## Context

Three real artifact types existed after Sprint 3
(`FrameExtractionArtifact`, `SceneCutArtifact`,
`TranscriptSegmentArtifact`), the precondition Sprint 2/3 set for
starting the Knowledge Builder layer (`docs/architecture/LAYERS.md`
Layer 4) rather than designing it against imagined data. The question
was how much to build first: `docs/architecture/DOMAIN_MODEL.md`
imagines Character Builders, Location Builders, Dialogue Builders,
Object Builders, Timeline Builders — a lot of surface area, none of it
implemented, all of it downstream of a more basic question nothing had
answered yet: does the `Artifact -> Entity` contract even hold up
against real, non-imagined artifact shapes?

## Decision

The first Knowledge Builder (`SceneGroupingBuilder`) does exactly one
thing: group `FrameExtractionArtifact` and `TranscriptSegmentArtifact`
into the `SceneCutArtifact` time ranges they overlap, producing one
`SceneEntity` per detected scene. No character tracking, no location
inference, no dialogue attribution — those all require the grouping
question to be answered first (frames and dialogue need to be
associated with a scene before anything can reason about who's in it).

Two new base types were introduced to support this, deliberately
mirroring `Artifact`/`Media`'s existing immutability discipline rather
than inventing a new pattern:

- `Entity` (`sceneforge/knowledge/entity.py`) — the Knowledge layer's
  analogue to `Artifact`: immutable, has `parents` (which Artifact ids
  it was built from, same shape as `Artifact.parents`), carries a
  `payload` and `metadata`.
- `KnowledgeBuilder` Protocol (`sceneforge/knowledge/builder.py`) —
  `name`/`version`/`build(artifacts) -> list[Entity]`, deliberately
  parallel to the `Provider` Protocol's `name`/`version`/`run()`.

`SceneGroupingBuilder` requires at least one `SceneCutArtifact` to
group by — it does not attempt to guess scene boundaries from frame
timestamps alone, per `docs/ARCHITECTURAL_PRINCIPLES.md` ("prefer
boring over clever"). Transcript segments spanning a scene cut are
assigned to *both* overlapping scenes rather than arbitrarily split at
the cut point, since a real line of dialogue crossing a hard cut
genuinely belongs to both.

## Consequences

- The `Artifact -> Entity` contract is now proven against real
  provider output, not just designed on paper — see
  `tests/knowledge/test_scene_grouping_integration.py`, which runs
  real `ffmpeg` frame extraction and real `scenedetect` scene
  detection (plus a fake-model `WhisperTranscribeProvider`, per
  ADR-0010) through actual `Pipeline` instances and feeds the results
  into `SceneGroupingBuilder`.
- `Entity` has no persistence layer yet (`ArtifactStore` from
  ADR-0008 only handles `Artifact`). This is a known, deliberate gap —
  see `.ai/PROJECT_STATE.md`'s open RFCs — not an oversight; building
  entity persistence before a second Knowledge Builder exists risks
  the same premature-formalization mistake Sprint 2 corrected away
  from with providers.
- Character/Location/Dialogue/Object/Timeline builders remain
  unimplemented, on purpose. `docs/architecture/DOMAIN_MODEL.md` now
  marks them explicitly as illustrative, not current.

## Alternatives Considered

1. Build a general-purpose "entity extraction" builder configurable
   for any grouping strategy, rather than a scene-specific one —
   rejected: there's exactly one real grouping need proven right now
   (frames/dialogue by scene); generalizing before a second concrete
   need exists would be designing the abstraction from imagination
   again, the exact mistake this ADR exists to avoid repeating.
2. Attempt character or location grouping in this first pass, since
   they're arguably more valuable end products — rejected: both
   require frame/dialogue-to-scene association as a prerequisite step,
   which this ADR's scope *is* that prerequisite. Attempting them
   first would mean building on an unproven `Artifact -> Entity`
   contract.
