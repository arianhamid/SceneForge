# Next Task

## Genesis Sprint 13

### Current Objective

Sprint 12 delivered the first real Application (`SceneSummary`),
an architecture-enforcing test suite, a utility provider
(`MediaHashProvider`), and knowledge-entity validation — all real,
tested, and verified. ADR-0021 then reconciled a much larger vision
(the "Understanding Ladder": Evidence → Facts → Entities → Events →
State → Relationships → Intentions → Narrative → Themes) against this
project's established discipline: adopt what's already real as
vocabulary, document the rest as direction with explicit trigger
conditions, build nothing ahead of a real data source. Sprint 13's
objective is the first rung of that ladder that isn't built yet:
**Facts**, which requires a provider that produces something above
raw detection.

Sprint 13 has since delivered real Tesseract OCR and `SceneTextBuilder`
(ADR-0022). That work expands and organizes Evidence but does not interpret it
into objective Facts, so the captioning/object-detection objective below remains
unchanged.

---

## Completed (Sprints 1-12)

- Layers 0-3: four real providers across two domains (`ffmpeg`,
  `scenedetect`, `whisper`, `opencv`), plus `MediaHashProvider`
  (content hashing, no external dependency).
- Layer 4: three real Knowledge Builders (`SceneGroupingBuilder`,
  `SceneFaceBuilder`, `SceneMergeBuilder`), `SceneSequenceBuilder` for
  relationships, `EntityStore` persistence/querying measured four
  times at real scale (ADR-0012, 0014, 0018, 0019).
- `sceneforge/knowledge/validation.py` — structural validation for
  entities (orphan scenes, self-references, duplicate indices,
  timeline checks), returning typed `ValidationIssue`s.
- `Entity.provenance` (`Provenance`: builder, source_artifact_ids,
  confidence) — real, shipped, independently converging with the
  world-model vision document's "every fact remembers why the system
  believes it."
- **First real Application**: `sceneforge.applications.scene_summary.SceneSummary`
  — reads real scene entities from an `EntityStore`, renders a
  Markdown summary. Proves `docs/philosophy/VISION.md`'s own success
  definition for the first time.
- **Architecture test suite** (`tests/architecture/test_import_rules.py`)
  — AST-based enforcement of the real dependency graph (core/knowledge/
  media/runtime/contrib boundaries), including a `TestKnownDependencies`
  class that positively asserts the real, deliberate ADR-backed
  dependencies (e.g. `core.pipeline` → `runtime.ProcessingContext`,
  `knowledge` → specific `contrib` artifact types) are never
  accidentally flagged.
- ADR-0020 (stable API surface), ADR-0021 (world-model vocabulary
  reconciliation — the Understanding Ladder now documented in
  `docs/architecture/DOMAIN_MODEL.md`, each rung marked real or
  blocked-on-what).

---

## Immediate Tasks

1. **A real `CAPTION` or `OBJECT_DETECTION` provider** — the actual
   blocker named explicitly in ADR-0021 for the Facts rung. A
   captioning model is the more direct path to "character speaks" /
   "door opens"-style Facts; follow ADR-0010's dependency-injection
   pattern if it needs downloaded weights (most captioning VLMs will),
   the same way `WhisperTranscribeProvider` was built.
2. **A minimal `FactExtractionBuilder`** (or similarly named
   `KnowledgeBuilder`) once (1) exists — turning caption/detection
   Artifacts into `Fact`-kind Entities. Keep it as narrow as
   `SceneGroupingBuilder` was on day one: one real transformation,
   proven against real provider output, not a general Fact-extraction
   framework.
3. Do **not** start Events, State, Relationships-beyond-scenes,
   Intentions, Narrative, or Themes yet — every one of them is
   transitively blocked on Facts existing first (ADR-0021's table).
   Building any of them before (1) and (2) are real would repeat the
   exact mistake this project has now avoided nine separate times.

---

## Coding Order

1. `sceneforge/contrib/<captioning-model>/` — new real provider,
   `docs/guides/ADDING_A_PROVIDER.md` step 3's injection pattern if
   weights aren't bundled (check bundled-vs-downloaded first, per
   ADR-0015's lesson — don't assume injection is needed by default)
2. `sceneforge/knowledge/fact_extraction_builder.py` — only once (1)
   has real output to build from
3. A real integration test combining (1) and (2) against a real image/
   video, the same discipline as every prior Knowledge Builder

---

## Success Criteria

- [ ] A real captioning or object-detection provider exists, with
      tests matching `docs/guides/ADDING_A_PROVIDER.md`'s checklist.
- [ ] A first real `Fact`-producing Knowledge Builder exists, proven
      against that provider's real output via integration test.
- [ ] `docs/architecture/DOMAIN_MODEL.md`'s Understanding Ladder entry
      for "Facts" is updated from "Not built" to real, with the same
      honesty about what's still blocked above it.
