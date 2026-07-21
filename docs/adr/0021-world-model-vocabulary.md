# ADR 0021: The World-Model Vision Is Adopted as Vocabulary and Direction, Not as Structure — Yet

## Status

Accepted

## Context

A vision document ("SceneForge should model movies like humans remember
them") proposes a nine-layer ladder — Evidence, Facts, Entities, Events,
State, Relationships, Intentions, Narrative, Themes — feeding a central
`WorldModel` object that owns provenance, uncertainty, and evidence
permanence, with Applications querying the `WorldModel` rather than
touching artifacts directly.

This is a genuinely good piece of thinking. It names something the
project's own `DOMAIN_MODEL.md` had only gestured at ("Knowledge
Graph", "Intelligence") in much coarser terms, and it independently
arrives at two ideas this project already needed:

1. **Provenance/confidence per fact.** `Entity.provenance` (a
   `Provenance` dataclass: `builder`, `source_artifact_ids`,
   `confidence`) already exists in `sceneforge/knowledge/entity.py`,
   added as a small, optional, backward-compatible field — independently
   converging on the vision document's "every fact should remember why
   the system believes it."
2. **Evidence permanence.** Already structurally true: `Artifact` is
   immutable and never deleted; `Entity.parents` traces every synthesis
   back to the artifacts it came from. Nothing in this codebase has ever
   overwritten a raw observation to update a conclusion — corrections
   are new artifacts/entities with `parents`, not mutations.

The question this ADR answers: how much of the rest of the document —
the remaining seven layers, and the central `WorldModel` type — should
be adopted now, versus documented as direction and built when a real
need appears, per the discipline established across ADR-0011 through
ADR-0019 (build the smallest real thing; check whether an existing
shape covers a new need before inventing one; four consecutive
real measurements found `Entity` + `EntityStore` + plain iteration
sufficient for everything asked of it so far).

## Decision

**Adopted now, as vocabulary and as already-real:**

| Vision document term | Maps to | Status |
|---|---|---|
| Evidence | `Artifact` | Real, four providers deep |
| Entities (persistent, cross-scene) | `Entity` | Real, `SceneGroupingBuilder`/`SceneFaceBuilder`/`SceneMergeBuilder` |
| "why does the system believe this" | `Entity.provenance` | Real, already shipped |
| "evidence never disappears" | `Artifact`/`Entity` immutability + `parents` | Real, structural, always true |
| Relationships between entities | `EntityKind.RELATIONSHIP` + `RelationshipBuilder` | Real, `SceneSequenceBuilder`/`SceneMergeBuilder` |

**Adopted as documented direction, not built yet — each with an
explicit trigger condition, not a timeline:**

| Vision document layer | Real trigger to start building it |
|---|---|
| Facts (objective, higher-level than Evidence: "Character A speaks", "door opens") | A provider that produces something above raw detection — the moment `CAPTION` or `OBJECT_DETECTION` ships real, this becomes buildable the same way `SceneFaceBuilder` became buildable once `FACE_DETECTION` shipped. Until then there is no real Fact source. |
| Character/Object/Location entities that persist and accumulate evidence across scenes | Requires re-identification (the same face/character recognized across non-adjacent scenes), which requires a real embedding or recognition provider that doesn't exist yet. `EntityKind.CHARACTER`/`LOCATION` already exist in the enum as forward declarations. |
| Events ("John enters room") | Requires Facts to exist first — an Event is a structured composition of Facts, per the vision document's own layering. Blocked transitively on the same gap as Facts. |
| State ("door: closed → opened → destroyed") | Requires Events to exist first, for the same reason. |
| Intentions, Narrative, Themes | Explicitly the vision document's own words: "These are inferred. Not extracted" / "This is interpretation." These require an LLM-reasoning step over a populated knowledge graph that doesn't exist yet (no Facts, no Events). Building this now would mean interpreting nothing. |
| Central `WorldModel` query object | Four real, differently-shaped measurements (ADR-0012, 0014, 0018, 0019) found `Entity` + `EntityStore` + `iter_all_entities()`/`find_related()` sufficient for targeted lookup, cross-domain correlation, cross-builder merge, and full-library aggregation, at real measured scale (0.125s–0.391s across thousands of entities). A dedicated `WorldModel` type would duplicate that without a demonstrated gap. **Trigger to revisit:** a real query `iter_all_entities()`/`find_related()` cannot answer — e.g. genuine multi-hop graph traversal ("everyone connected to a location John visited who also appeared in a scene with Mary") — attempted for real and measured to be actually awkward or slow, the same way `EntityStore.keys()` got added only once a real spike showed it was missing. |

**Not adopted, explicitly:** rewriting `Artifact`/`Entity` to be
literally renamed `Evidence`/`Fact` to match the document's vocabulary.
The concepts map cleanly (see table above); renaming working, tested
types across four real providers and eleven ADRs for vocabulary
alignment alone would cost real breakage for zero behavioral change.

## Consequences

- `docs/architecture/DOMAIN_MODEL.md` gains the fuller ladder
  (Evidence → Facts → Entities → Events → State → Relationships →
  Intentions → Narrative → Themes) as documented vocabulary, each term
  marked with its real/aspirational status and — for aspirational
  ones — its trigger condition, so a future contributor has language
  for "which layer am I building" without any layer being scaffolded
  in code before it has real data to run on.
- `docs/philosophy/VISION.md` is not rewritten — its principles
  (architecture before implementation but prove it first; capabilities
  before models; no hidden state) already cover why this ADR sequences
  things the way it does. This ADR is the applied instance of those
  principles against a much bigger vision than any prior one.
- The next real capability gap this unblocks is unchanged from
  `.ai/NEXT_TASK.md`'s existing assessment: a `CAPTION` or
  `OBJECT_DETECTION` provider is the actual next step toward Facts,
  the same as it was the actual next step toward a second Knowledge
  Builder in Sprint 8. This ADR doesn't change the priority — it gives
  that priority a longer runway of justified direction behind it.

## Alternatives Considered

1. **Adopt the full nine-layer structure now, including a `WorldModel`
   type, as scaffolding for future providers to fill in.** Rejected —
   this is precisely Phase 1 of the earlier "v9" plan's mistake
   (`RuntimeServices` with zero real consumers), at nine times the
   scale. Every layer above Entities would have zero real data source
   the day it's merged.
2. **Reject the vision document's framing entirely and keep
   `DOMAIN_MODEL.md` as-is.** Rejected — the document is right about
   two things this project hadn't fully named (provenance, evidence
   permanence), and even where it's ahead of the codebase, the
   vocabulary itself is worth documenting so future work has a map,
   as long as the map is honestly marked with what's real.
