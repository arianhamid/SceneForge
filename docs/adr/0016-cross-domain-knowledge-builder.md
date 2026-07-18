# ADR 0016: Cross-Domain Knowledge Builders Correlate by Artifact Fields, Not a New Protocol

## Status

Accepted

## Context

Sprint 8 (ADR-0015) shipped a real image-domain provider
(`OpenCVFaceDetectionProvider`) but deliberately deferred the second
Knowledge Builder it was meant to unblock, flagging a real open
question: a `FaceDetectionArtifact`'s `media_id` belongs to whatever
single-frame `ImageMedia` was decoded to detect it — not the source
video's `media_id` — since each extracted frame is loaded and
processed as its own independent `ImageMedia`. Building a Knowledge
Builder that groups faces into scenes means correlating across that
media_id mismatch somehow. The suspicion going in (recorded in
ADR-0015) was that this might need a third builder Protocol shape,
beyond `KnowledgeBuilder` (`Artifact -> Entity`, ADR-0011) and
`RelationshipBuilder` (`Entity -> Entity`, ADR-0013) — one that takes
*both* pre-built Entities (to know which frames belong to which scene)
*and* Artifacts (the raw face detections).

## Decision

**No new Protocol was needed.** `SceneFaceBuilder` is a plain
`KnowledgeBuilder` — the same `build(artifacts: list[Artifact]) ->
list[Entity]` shape as `SceneGroupingBuilder`.

The resolution: `FaceDetectionArtifact` gained a `source_frame_path`
field, populated automatically by `OpenCVFaceDetectionProvider` from
the decoded image's own `metadata["source"]`. When that `ImageMedia`
is a still frame extracted from a video (rather than a standalone
photo), `source_frame_path` is exactly the same string as
`FrameExtractionArtifact.frame_path` — both point at the same file on
disk. `SceneFaceBuilder` correlates by matching those two path strings
for equality, the same way `SceneGroupingBuilder` correlates frames
and transcript segments by numeric time-range overlap. `media_id`
never needs to match, and is never used for this correlation at all.

This means the anticipated "Entity + Artifact -> Entity" third shape
didn't materialize — because the actual correlating key
(`source_frame_path`) was already available on the Artifact the whole
time, once the provider was taught to carry it forward. The fix lived
one layer down from where the problem first looked like it was.

## Consequences

- `SceneFaceBuilder` (`sceneforge/knowledge/scene_face_builder.py`) is
  SceneForge's first Knowledge Builder synthesizing across two
  capability domains at once (video/scene structure and image/face
  detection), and it required zero changes to `KnowledgeBuilder`,
  `Entity`, or `EntityStore` — everything from ADR-0011/0012 held up
  under a genuinely different real use.
- The general pattern this establishes for future cross-domain
  builders: when a provider's output needs to be correlated back to a
  different domain's structure, check whether the provider can carry
  forward an existing correlating field (a file path, a timestamp)
  *before* assuming a new builder Protocol shape is needed. Adding the
  field to the Artifact is cheap; adding a new Protocol is not.
- `docs/guides/ADDING_A_PROVIDER.md` should note this pattern for the
  next provider author whose output needs correlating across domains.
- This closes Sprint 8's deferred item honestly rather than having
  forced it — the spike (this ADR) took a dedicated pass, and found a
  simpler answer than the one anticipated when it was deferred.

## Alternatives Considered

1. **Relink `FaceDetectionArtifact.media_id` to the video's media_id**
   via `dataclasses.replace()`, mirroring how
   `tests/knowledge/test_scene_grouping_integration.py` relinked
   `TranscriptSegmentArtifact.media_id`. Rejected once `source_frame_path`
   correlation proved sufficient — relinking `media_id` would have
   worked too, but would have overloaded `media_id` to mean two
   different things (the artifact's own media vs. a "logical" media it
   should be grouped under) rather than adding a field whose meaning
   is unambiguous.
2. **A new `CompositeBuilder` Protocol taking both `list[Entity]` and
   `list[Artifact]`.** Not built — the correlation didn't end up
   needing pre-built Entities as input at all, so this was solving a
   problem that turned out not to exist. If a future cross-domain
   builder genuinely does need to reference already-built Entities
   (not just raw Artifacts), that's real evidence to design this then.
