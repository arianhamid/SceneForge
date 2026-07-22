# Next Task

## Genesis Sprint 14

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
into objective Facts, so the captioning/object-detection objective below
remains the eventual target — but a 2026-07-22 implementation review of the
comprehensive movie-understanding research direction reproduced live defects
in the identity and evidence foundation that objective would be built on
(random `Media.id` in `content_key()`, unserializable `Provenance`, no way to
resolve a conclusion back to its evidence, nested "immutable" payloads that
mutate in place). ADR-0024 inserts a Phase 0 ahead of the captioning/
object-detection provider to fix that foundation first. `Entity.provenance`
now round-trips through `EntityStore`; the rest of Phase 0 is next.

---

## Completed (Sprints 1-13)

- Layers 0-3: five real feature providers across video/audio and image domains
  (`ffmpeg`, `scenedetect`, `whisper`, `opencv`, `tesseract`), plus the
  dependency-free `MediaHashProvider` utility.
- Layer 4: three Artifact-to-Entity Knowledge Builders
  (`SceneGroupingBuilder`, `SceneFaceBuilder`, `SceneTextBuilder`) and two
  Entity-to-Entity Relationship Builders (`SceneSequenceBuilder`,
  `SceneMergeBuilder`). `EntityStore` persistence/querying has been measured
  four times at real scale (ADR-0012, 0014, 0018, 0019).
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

## Immediate Tasks (ADR-0024 Phase 0, in order)

1. **Provenance round-trips through `EntityStore`.** Done —
   `sceneforge/knowledge/storage.py` now serializes/deserializes
   `Provenance`; see `tests/knowledge/test_storage.py`.
2. **Redesign `content_key()`'s identity basis**: content identity
   (derived from file bytes or a documented normalized-asset hash, not
   a random `Media.id`) plus an execution fingerprint (provider/schema
   version, model ID/revision, prompt/template version, sampling/
   preprocessing/inference configuration, tool/library versions).
   Reserve edition identity for provenance/run scope rather than making
   later external matching invalidate byte-derived cache entries. This is
   a deliberate breaking change; existing local caches are invalidated,
   not migrated. Implement the Media identity contract and provider
   execution descriptor, then update Pipeline/AsyncPipeline and tests.
3. **A minimal typed evidence contract**: `EvidenceAnchor` and
   `EvidenceLink`, plus `ArtifactStore` lookup by artifact ID and by
   media. No graph database — an indexed or SQLite-backed spike is
   enough, per the ADR-0014/0019 precedent.
4. **Separate the cache role from the evidence role**: keep
   `FileArtifactStore`/`FileEntityStore` as an evictable computation
   cache; add a distinct durable, revision-aware evidence/knowledge
   record concept, even if initially backed by the same file format.
5. **A minimal `AnalysisRun` manifest**: provider/model/config
   versions, attempted/skipped/failed intervals, cache-hit vs.
   fresh-run status per stage.

Only once 2–5 are real and tested:

6. **A real `CAPTION` or `OBJECT_DETECTION` provider** — the actual
   blocker named explicitly in ADR-0021 for the Facts rung. A
   captioning model is the more direct path to "character speaks" /
   "door opens"-style Facts; follow ADR-0010's dependency-injection
   pattern if it needs downloaded weights (most captioning VLMs will),
   the same way `WhisperTranscribeProvider` was built.
7. **A minimal `FactExtractionBuilder`** (or similarly named
   `KnowledgeBuilder`) once (6) exists — turning caption/detection
   Artifacts into `Fact`-kind Entities, anchored through the evidence
   contract from (3). Keep it as narrow as `SceneGroupingBuilder` was
   on day one: one real transformation, proven against real provider
   output, not a general Fact-extraction framework.
8. Do **not** start Events, State, Relationships-beyond-scenes,
   Intentions, Narrative, or Themes yet — every one of them is
   transitively blocked on Facts existing first (ADR-0021's table).
   Building any of them before (6) and (7) are real would repeat the
   exact mistake this project has now avoided nine separate times.

Provider-neutral artifact contracts and the Runtime decoding-boundary gap are
explicitly deferred past Phase 0. The first provider for a new capability may
define a concrete output; normalize it only when a second implementation of the
same capability provides another real case to design against.

---

## Coding Order

Phase 0 (ADR-0024), in order — items 2–5 of the Immediate Tasks above:

1. `sceneforge/media/` (content and edition identity), the Provider execution
   descriptor, `sceneforge/core/storage.py` (`content_key()`), and the sync/
   async Pipeline cache call sites. Content identity plus execution fingerprint
   drives the computation cache; edition identity remains provenance/run scope.
   This is a breaking change, so update the related contract and cache tests.
2. A minimal typed evidence contract (`EvidenceAnchor`, `EvidenceLink`
   with `(kind, id)` endpoints) plus artifact lookup by ID/media.
3. Split the evictable computation-cache role from a durable,
   revision-aware evidence/knowledge record.
4. A minimal `AnalysisRun` manifest.

Only once 1–4 above are real and tested, start Phase 1:

5. `sceneforge/contrib/<captioning-model>/` — new real provider,
   `docs/guides/ADDING_A_PROVIDER.md` step 3's injection pattern if
   weights aren't bundled (check bundled-vs-downloaded first, per
   ADR-0015's lesson — don't assume injection is needed by default)
6. `sceneforge/knowledge/fact_extraction_builder.py` — only once (5)
   has real output to build from, anchored through the evidence
   contract from item 2 above
7. A real integration test combining (5) and (6) against a real image/
   video, the same discipline as every prior Knowledge Builder

---

## Success Criteria

Phase 0 (ADR-0024):

- [ ] `content_key()` derives from content identity plus an execution
      fingerprint, not a random `Media.id`; reloading the same
      unchanged file is a cache hit, two differently configured
      provider runs are not a false hit.
- [x] `Provenance` round-trips through `EntityStore` — done, see
      `tests/knowledge/test_storage.py`.
- [ ] A typed `EvidenceAnchor`/`EvidenceLink` contract exists with
      artifact lookup by ID and by media; an application can resolve a
      stored conclusion back to the source evidence that supports it.
- [ ] The evictable computation cache and durable evidence/knowledge
      record are distinct concepts, even if backed by the same file
      format initially.
- [ ] A minimal `AnalysisRun` manifest records provider/model/config
      versions and per-stage attempted/skipped/failed/cache-hit status.

Phase 1, once Phase 0 above is real:

- [ ] A real captioning or object-detection provider exists, with
      tests matching `docs/guides/ADDING_A_PROVIDER.md`'s checklist.
- [ ] A first real `Fact`-producing Knowledge Builder exists, proven
      against that provider's real output via integration test, and
      anchored through the Phase-0 evidence contract. Its typed payload
      is deeply immutable; the known nested-metadata defect is not carried
      into the first production-ready Fact contract.
- [ ] `docs/architecture/DOMAIN_MODEL.md`'s Understanding Ladder entry
      for "Facts" is updated from "Not built" to real, with the same
      honesty about what's still blocked above it.
