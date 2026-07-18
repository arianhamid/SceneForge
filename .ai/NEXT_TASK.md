# Next Task

## Genesis Sprint 12

### Current Objective

Four consecutive spikes (Sprints 8-11) found the existing
`Entity`/`EntityStore` shape sufficient for cross-domain correlation,
cross-builder merging, and cross-video querying, at real measured
scale. For the first time, Layer 5 (Knowledge Graph) has no obviously
overdue gap. Per `docs/philosophy/VISION.md`'s own definition of
success — "someone runs a real movie through SceneForge once, then
builds three different things... from that single analysis" — the
honest next step is not a fifth spike on the same question. It's
building the first real Application: the smallest real consumer of
the knowledge this framework now actually produces.

---

## Completed (Sprints 1-11)

- Layers 0-3: four real providers across two domains (`ffmpeg`,
  `scenedetect`, `whisper`, `opencv`).
- Layer 4: three real Knowledge Builders (`SceneGroupingBuilder`,
  `SceneFaceBuilder` cross-domain, `SceneMergeBuilder` cross-builder),
  plus `SceneSequenceBuilder` for relationships. `EntityStore`
  persistence and querying, measured four separate times at real
  scale (ADR-0012, 0014, 0018, 0019) with no gap found yet.
- Registry/Pipeline RFC closed (ADR-0017).
- `examples/end_to_end/analyze_video.py`: full chain — providers,
  three knowledge-layer stages, merge, all caches — proven against
  real video.

---

## Immediate Tasks

1. **Build the first real Application** — Layer 7, skipping the
   as-yet-unproven need for Layers 5/6 (Knowledge Graph, Intelligence)
   as dedicated infrastructure, since nothing has shown they need to
   be more than "call `iter_all_entities()`/`find_related()` and
   filter in Python" so far. The smallest real candidate: a script
   that takes a processed video's `FileEntityStore` and produces a
   human-readable scene-by-scene summary (dialogue + face count +
   sequence) — proving `docs/philosophy/VISION.md`'s actual success
   criterion for the first time, not just its infrastructure.
2. If (1) reveals a real need for something Layers 5/6 would provide
   (e.g. genuine multi-hop graph traversal, not just filtering), that's
   real evidence — build it then, the same discipline as every prior
   sprint.
3. `CAPTION`/`OCR`/`OBJECT_DETECTION` remain unimplemented capabilities.
   Only add one if the Application from (1) creates a concrete need for
   richer entity content than scene structure + face counts — not
   speculatively.

---

## Coding Order

1. `examples/applications/scene_summary.py` (or similar) — a real,
   runnable Application consuming a real processed video's entities
2. Only if (1) surfaces a real gap: whatever Layer 5/6 infrastructure
   it actually needs

---

## Success Criteria

- [ ] A real Application exists, consuming real `Entity` data from a
      real processed video (not synthetic fixtures), and produces
      genuinely useful output a person would want — the first time
      this project's own stated definition of success
      (`docs/philosophy/VISION.md`) has actually been demonstrated
      end-to-end rather than just built toward.
