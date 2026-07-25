# Session Changes: ADR-0024 Phase 0 → Phase 1 (Facts Rung)

Summary of all work completed in this session, in chronological order.
Written for use as a commit message / PR description — each section
maps roughly to one logical commit if you want to split it up.

---

## 1. Verified and corrected the 2026-07-22 implementation review

- Reproduced the review's top findings live (random `Media.id` in
  `content_key()`, unserializable `Provenance`, nested-metadata
  mutability) before trusting them.
- Fixed **provenance round-tripping**: `entity_to_dict`/`entity_from_dict`
  in `sceneforge/knowledge/storage.py` now serialize/deserialize
  `Provenance` correctly (previously raised `TypeError` on save).
- Wrote **ADR-0024**: "Phase 0 — Trustworthy Identity, Evidence, and
  Run Provenance," defining five deliverables ahead of the
  captioning/object-detection provider originally planned as
  Phase 1.
- A follow-up, independently-authored review of *this* work found and
  I fixed: weak round-trip tests that didn't actually exercise JSON
  serialization, missing error-boundary translation for malformed
  provenance data, an internal "four parts" vs. five-item mismatch in
  the ADR, and under-specified `EvidenceLink` endpoints.

## 2. ADR-0024 Phase 0 — all five items shipped

1. **Provenance round-trips through `EntityStore`.** (above)
2. **`content_key()` redesign**: replaced the random per-load
   `Media.id` with real content identity (file-bytes hash, documented
   name-based fallback for media with no backing file) plus a new
   `Provider.execution_fingerprint` property, folded into the cache
   key. `WhisperTranscribeProvider` overrides it with a hash of its
   `transcribe_kwargs` — the concrete collision case a prior review
   reproduced live. Breaking, deliberate cache invalidation.
3. **Typed evidence contract**: new `sceneforge/core/evidence.py`
   (`EvidenceAnchor`, `EvidenceLink`, typed `Reference`/`ReferenceKind`,
   `EvidenceRelation`), plus `ArtifactStore.keys()`,
   `find_artifact_by_id()`, `find_artifact_by_media()` in
   `core/storage.py`.
4. **Cache/evidence split**: new `KnowledgeRecordStore` in
   `sceneforge/knowledge/storage.py` (`FileKnowledgeRecordStore`,
   `InMemoryKnowledgeRecordStore`) — durable, append-only,
   revision-aware, distinct from `EntityStore`'s evictable cache role.
   `append()`/`retract()` only; no `put`/`delete`.
5. **`AnalysisRun` manifest**: new `sceneforge/runtime/analysis_run.py`
   (`AnalysisRun`, `StageRecord`, `StageOutcome`), wired as an opt-in
   `analysis_run` parameter into `Pipeline.run_detailed()` and
   `AsyncPipeline.run_detailed()`/`run_many()`. Records
   ATTEMPTED/SKIPPED/FAILED with cache-hit/fresh-run/retry/duration
   detail, without changing existing return/raise behavior when
   omitted.

All five items are proven with unit + integration tests, verified with
`pytest`, `ruff`, and `mypy --strict` after every step.

## 3. Phase 1 — the Facts rung, with two independent real inputs

- **`TransformersCaptionProvider`** (`sceneforge/contrib/transformers_caption/`):
  real `Capability.CAPTION` implementation wrapping an injected
  Hugging Face `transformers` `image-text-to-text` pipeline
  (dependency-injection pattern matching `WhisperTranscribeProvider`).
  The `ImageTextToTextPipelineProtocol` was modeled on the actual
  installed `transformers==5.14.1` source, not guessed.
- **`TransformersObjectDetectionProvider`**
  (`sceneforge/contrib/transformers_object_detection/`): the second
  real Facts-rung provider, built specifically to test whether the
  Fact-extraction shape generalizes. Confirmed a real design
  difference: an empty detection result is a valid outcome here,
  unlike an empty caption.
- **`FactExtractionBuilder`** (`sceneforge/knowledge/fact_extraction_builder.py`,
  new `EntityKind.FACT`): converts either artifact type into one
  `Fact`-kind Entity. The artifact-count shape ("one Artifact → one
  Fact") generalized across both providers; the statement-synthesis
  logic did not (dispatches per artifact type). `Provenance.confidence`
  got its first real, non-`None` value from detection scores.
- Proven end-to-end against a **real ffmpeg-generated image**, not
  just fakes (`tests/knowledge/test_fact_extraction_integration.py`).
- **`SceneSummary`** (`sceneforge/applications/scene_summary.py`)
  extended to render Facts as their own section — closing the loop
  from provider to visible output for the first time. Verified working
  for object-detection-derived Facts with zero code changes.

## 4. Bugs found and fixed along the way

- `TransformersObjectDetectionProvider` declared
  `ObjectDetectionArtifact.source_frame_path` but never populated it
  (silently always `""`).
- `CaptionArtifact` had no `source_frame_path` field at all, unlike
  the other three per-frame detection artifacts
  (`FaceDetectionArtifact`, `OCRTextArtifact`,
  `ObjectDetectionArtifact`). Added and wired it, and threaded it
  through into `FactExtractionBuilder`'s Fact metadata.
- `sceneforge/contrib/tesseract/__init__.py`'s docstring claimed OCR
  was "the first real capability toward the Facts rung," directly
  contradicting ADR-0022's own title ("Still Evidence Not Facts").
  Corrected.
- **`examples/end_to_end/analyze_video.py` crashed** with an unhandled
  `OSError` when `transformers` was installed but model weights were
  unreachable (no network / no cached weights) — found by actually
  running the script against a real ffmpeg-generated video, not just
  reading the code. The `try/except ImportError` guard only covered
  the *imports*; the actual pipeline-construction calls (where the
  network/torch failures happen) were unguarded. Fixed with a broader
  exception guard around model loading, matching the graceful-skip
  pattern already used for every other optional step in that script.
- Two documentation duplication bugs in `.ai/PROJECT_STATE.md` left
  over from earlier edits in this session (a repeated "N real feature
  providers" bullet, and a repeated "not verified against downloaded
  weights" bullet) — caught and merged.

## 5. `examples/end_to_end/analyze_video.py` extended

Added, each gracefully optional and skipped with a clear message if
unavailable:

- Real Tesseract OCR (`TesseractOCRProvider` + `SceneTextBuilder`)
- Real captioning + object detection (the actual Facts-rung step) via
  a new `--no-facts` CLI flag, since this is the one step needing real
  network access to the Hugging Face Hub
- Final `SceneSummary` render, showing scenes and Facts together
- Extended the existing "run twice, prove caching works" section to
  cover the new caches too

Verified by actually running it against a real ffmpeg-generated video
in this environment (not just syntax-checked).

## 6. Documentation

Every step above was accompanied by updates to `.ai/PROJECT_STATE.md`,
`.ai/NEXT_TASK.md`, `docs/architecture/DOMAIN_MODEL.md`'s Understanding
Ladder, and `docs/specifications/PROVIDER_SPEC.md`, kept consistent
with a full stale-reference sweep after each major change — including
fixing a couple of pre-existing inconsistencies unrelated to this
session's own work (a stale provider count, an outdated "blocked on
Facts" claim on the Events rung entry, now that Facts is real).

---

## Final verification

```
516 passed, 1 skipped
ruff check: all checks passed
ruff format --check: all files formatted
mypy --strict: no issues found in 92 source files
```

## New public API surface

- `sceneforge.core`: `EvidenceAnchor`, `EvidenceLink`, `EvidenceRelation`,
  `Reference`, `ReferenceKind`, `find_artifact_by_id`,
  `find_artifacts_by_media`
- `sceneforge.knowledge`: `FactExtractionBuilder`, `KnowledgeRecord`,
  `KnowledgeRecordStore`, `FileKnowledgeRecordStore`,
  `InMemoryKnowledgeRecordStore`, `EntityKind.FACT`
- `sceneforge.runtime`: `AnalysisRun`, `StageRecord`, `StageOutcome`
- `sceneforge.contrib.transformers_caption`: `CaptionArtifact`,
  `TransformersCaptionProvider`, `ImageTextToTextPipelineProtocol`
- `sceneforge.contrib.transformers_object_detection`:
  `ObjectDetectionArtifact`, `TransformersObjectDetectionProvider`,
  `ObjectDetectionPipelineProtocol`
- `Provider.execution_fingerprint` (new property on the ABC and both
  structural `Provider`/`AsyncProvider` protocols)
- `ArtifactStore.keys()` (new protocol member)

## Breaking changes

- `content_key()` gained a fourth parameter (`execution_fingerprint`,
  defaults to `""` — backward compatible) and changed its identity
  basis. **Existing local caches are invalidated**, not migrated; this
  was a deliberate decision (ADR-0024 item 2), not an oversight.
