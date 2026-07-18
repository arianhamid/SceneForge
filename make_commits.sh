#!/usr/bin/env bash
# SceneForge — split one session's worth of changes into logical commits.
#
# HONESTY NOTE (read before running): this script was written by an AI
# that does not have access to this repo's real git history — only the
# final content of each file after the session. Files that were created
# once and never touched again (most providers, most ADRs, most tests)
# are committed cleanly and accurately. Files that were edited across
# many sprints in the session (README.md, CHANGELOG.md, SUMMARY.md,
# ARCHITECT_REVIEW.md, .ai/PROJECT_STATE.md, .ai/NEXT_TASK.md,
# sceneforge/knowledge/__init__.py, sceneforge/knowledge/storage.py,
# examples/end_to_end/analyze_video.py, docs/specifications/*.md)
# cannot be split into per-sprint diffs without real intermediate
# snapshots, so they're swept into ONE final commit at the end rather
# than fake-attributed to a single sprint. Some earlier commits (e.g.
# the core-resilience one, which touches sceneforge/core/storage.py)
# may therefore contain slightly more than their title implies, because
# that file's *final* content is what gets staged the first time it's
# touched. This is called out in the affected commit bodies below.
#
# Run from the repo root, after copying the session's files over the
# existing repo (see instructions in chat).

set -euo pipefail

if [ ! -d .git ]; then
  echo "Run this from the root of your git repo (no .git found here)." >&2
  exit 1
fi

BRANCH="feature/architecture-hardening-sprints-2-11"
git checkout -b "$BRANCH" 2>/dev/null || git checkout "$BRANCH"

# Stage only paths that exist and have changes; skip quietly otherwise
# so re-running this script (or running it out of order) is safe.
add() {
  for path in "$@"; do
    if [ -e "$path" ]; then
      git add -- "$path"
    fi
  done
}

commit_if_staged() {
  if ! git diff --cached --quiet; then
    git commit -m "$1"
  else
    echo "Nothing staged for: $1 (skipping)"
  fi
}

# ---------------------------------------------------------------------
# 1. Core resilience: Pipeline, CapabilityRegistry, MediaEnricher,
#    ArtifactStore, AsyncPipeline, complete Provider Protocol, plugin
#    discovery
# ---------------------------------------------------------------------
add \
  sceneforge/core/enrichment.py \
  sceneforge/core/storage.py \
  sceneforge/core/async_provider.py \
  sceneforge/core/async_pipeline.py \
  sceneforge/core/pipeline.py \
  sceneforge/core/capability_registry.py \
  sceneforge/core/provider_protocol.py \
  sceneforge/core/exceptions.py \
  sceneforge/core/__init__.py \
  sceneforge/media/base.py \
  sceneforge/plugins/registry.py \
  sceneforge/contrib/audio_info/artifacts.py \
  sceneforge/contrib/image_info/artifacts.py \
  tests/core/test_pipeline_resilience.py \
  tests/core/test_capability_registry.py \
  tests/core/test_enrichment.py \
  tests/core/test_storage.py \
  tests/core/test_async_pipeline.py \
  tests/core/test_provider_protocol.py \
  tests/media/test_evolve.py \
  tests/plugins/test_plugin_discovery.py \
  tests/test_artifact.py \
  docs/adr/0003-pipeline-orchestration.md \
  docs/adr/0006-provider-protocol-completeness.md \
  docs/adr/0007-injectable-capability-registry.md \
  docs/adr/0008-artifact-persistence.md \
  docs/adr/0009-async-providers.md \
  pyproject.toml

commit_if_staged "core: injectable CapabilityRegistry, resilient Pipeline, MediaEnricher, ArtifactStore, AsyncPipeline

- Pipeline now actually does what ADR-0003 always claimed: timing,
  retries with backoff, ProcessingContext cancellation, provider
  errors wrapped in ProviderExecutionError instead of escaping raw.
- CapabilityRegistry replaces a module-level global dict + a
  Pipeline class flag with an injectable object (ADR-0007) — two
  Pipelines in one process can no longer silently affect each other.
- MediaEnricher + Media.evolve() give a sanctioned, immutable path
  from placeholder metadata (e.g. VideoMedia duration=0.0) to real
  metadata.
- ArtifactStore (file + in-memory) makes provider-result caching real
  and content-addressable, keyed by media identity + provider name +
  version (ADR-0008).
- AsyncProvider/AsyncPipeline add timeout, retry, and bounded
  concurrency for I/O- and GPU-bound providers (ADR-0009).
- provider_protocol.Provider now declares its full structural
  contract (name/version/capabilities/run), fixing a real gap where a
  run()-only class incorrectly satisfied isinstance() checks
  (ADR-0006).
- Plugin discovery via importlib.metadata.entry_points().

NOTE: sceneforge/core/storage.py's committed content includes
keys()/query-primitive-adjacent groundwork added later in the
session; see ADR-0008 for what belongs to this commit specifically."

# ---------------------------------------------------------------------
# 2. First real provider: ffmpeg frame extraction + ffprobe enrichment
# ---------------------------------------------------------------------
add \
  sceneforge/contrib/ffmpeg \
  tests/contrib/test_ffmpeg_integration.py

commit_if_staged "contrib: real frame-extraction provider via ffmpeg

FFmpegFrameExtractionProvider (Capability.FRAME_EXTRACTION) and its
companion FFprobeEnricher — the framework's first non-stub provider.
Real ffmpeg/ffprobe subprocess calls, integration tested against a
real generated video, not mocked."

# ---------------------------------------------------------------------
# 3. Second real provider: scenedetect
# ---------------------------------------------------------------------
add \
  sceneforge/contrib/scenedetect \
  tests/contrib/test_scenedetect_integration.py

commit_if_staged "contrib: real scene-detection provider via PySceneDetect

PySceneDetectProvider (Capability.DETECT_SCENES) — content-aware cut
detection, no model weights or network needed. Integration tests
found and documented a real behavior: the default min_scene_len
(15 frames) merges cuts shorter than ~1.5s; exposed as a tunable."

# ---------------------------------------------------------------------
# 4. Third real provider: whisper (dependency-injected)
# ---------------------------------------------------------------------
add \
  sceneforge/contrib/whisper \
  tests/contrib/test_whisper_transcribe.py \
  docs/adr/0010-dependency-injected-model-providers.md

commit_if_staged "contrib: real transcription provider via faster-whisper (ADR-0010)

WhisperTranscribeProvider (Capability.TRANSCRIBE). The model is
injected via a structural Protocol rather than constructed
internally, since constructing a real WhisperModel downloads weights
from the Hugging Face Hub — this makes the provider fully unit
testable without network access or a GPU."

# ---------------------------------------------------------------------
# 5. Knowledge layer: first Knowledge Builder
# ---------------------------------------------------------------------
add \
  sceneforge/knowledge/__init__.py \
  sceneforge/knowledge/builder.py \
  sceneforge/knowledge/entity.py \
  sceneforge/knowledge/exceptions.py \
  sceneforge/knowledge/scene_grouping_builder.py \
  tests/knowledge/test_entity.py \
  tests/knowledge/test_scene_grouping_builder.py \
  tests/knowledge/test_scene_grouping_integration.py \
  docs/adr/0011-first-knowledge-builder-scope.md

commit_if_staged "knowledge: first Knowledge Builder — SceneGroupingBuilder (ADR-0011)

Entity/EntityKind (Layer 4's immutable base type, mirroring Artifact)
and the KnowledgeBuilder Protocol. SceneGroupingBuilder groups frames
and transcript segments into detected scenes — deliberately scoped to
time-overlap grouping only, to prove the Artifact -> Entity contract
against real provider output before any wider ambition.

NOTE: __init__.py and builder.py are 'living' files extended in later
commits (build_with_cache, more builder exports); their content here
reflects the full session's final state, not just this step."

# ---------------------------------------------------------------------
# 6. Entity persistence
# ---------------------------------------------------------------------
add \
  sceneforge/knowledge/storage.py \
  tests/knowledge/test_storage.py \
  docs/adr/0012-entity-persistence.md

commit_if_staged "knowledge: Entity persistence via EntityStore (ADR-0012)

FileEntityStore/InMemoryEntityStore + entity_build_key(), resolving
whether Entity persistence should extend ArtifactStore or need its
own shape — built both and compared; a separate EntityStore won
because Artifact/Entity field names and cache-key bases genuinely
differ (single-media key vs. whole-input-set key).

NOTE: this file's committed content also includes keys() and the
iter_all_entities()/find_related() query primitives added later in
the session (see ADR-0014) — not separable without real diffs."

# ---------------------------------------------------------------------
# 7. Entity relationships
# ---------------------------------------------------------------------
add \
  sceneforge/knowledge/relationship_builder.py \
  tests/knowledge/test_relationship_builder.py \
  tests/knowledge/test_relationship_integration.py \
  docs/adr/0013-entity-relationships.md

commit_if_staged "knowledge: entity relationships — RelationshipBuilder, SceneSequenceBuilder (ADR-0013)

A relationship reuses the Entity shape (EntityKind.RELATIONSHIP,
parents pointing at the related Entity ids) but needs a separate
RelationshipBuilder Protocol from KnowledgeBuilder, since its input is
Entities (output of an earlier stage), not Artifacts. Proven against
a real three-scene video: scenedetect finds 3 cuts, SceneSequenceBuilder
correctly sequences them (0->1, 1->2)."

# ---------------------------------------------------------------------
# 8. Relationship query spike
# ---------------------------------------------------------------------
add \
  tests/knowledge/test_query_spike.py \
  docs/adr/0014-relationship-query-spike.md

commit_if_staged "knowledge: relationship querying measured at scale, not assumed (ADR-0014)

Found EntityStore had no way to enumerate its own contents before
this — get/put/has/delete all require an already-known key. Added
EntityStore.keys() (see commit 6's note) plus iter_all_entities()/
find_related(). Measured find_related() against a synthetic 300-movie,
11,700-entity dataset on real FileEntityStore disk I/O: 0.125s. No
index or graph library added — the measurement didn't call for one."

# ---------------------------------------------------------------------
# 9. Fourth real provider: opencv face detection
# ---------------------------------------------------------------------
add \
  sceneforge/contrib/opencv \
  tests/contrib/test_opencv_integration.py \
  docs/adr/0015-opencv-face-detection.md

commit_if_staged "contrib: real face-detection provider via OpenCV (ADR-0015)

OpenCVFaceDetectionProvider (Capability.FACE_DETECTION) using OpenCV's
bundled Haar cascade weights — no dependency injection needed, since
the weights ship inside the package (a real counter-example to
assuming every model-backed provider needs ADR-0010's injection
pattern). OpenCVImageEnricher also closes a real gap: ImageMedia has
had placeholder width=0/height=0 since the project's first sprint
with no enricher, unlike VideoMedia's FFprobeEnricher.

No real face photograph is available in this environment (no network
access); tests prove the mechanics and the negative path with
certainty, and the module docstring says so explicitly."

# ---------------------------------------------------------------------
# 10. Cross-domain Knowledge Builder + Registry/Pipeline RFC closure
# ---------------------------------------------------------------------
add \
  sceneforge/knowledge/scene_face_builder.py \
  sceneforge/contrib/opencv/face_detection_artifact.py \
  sceneforge/contrib/opencv/face_detection_provider.py \
  tests/knowledge/test_scene_face_builder.py \
  tests/knowledge/test_scene_face_integration.py \
  docs/adr/0016-cross-domain-knowledge-builder.md \
  docs/adr/0017-registry-pipeline-rfc-closed.md

commit_if_staged "knowledge: cross-domain Knowledge Builder (ADR-0016); close Registry/Pipeline RFC (ADR-0017)

SceneFaceBuilder is the first Knowledge Builder synthesizing across
two capability domains (video/scene structure + image/face
detection). Expected to need a third builder Protocol shape (Entity +
Artifact -> Entity); didn't — FaceDetectionArtifact.source_frame_path
(set by the provider from the image's own metadata) already matches
FrameExtractionArtifact.frame_path, so plain KnowledgeBuilder
sufficed. Proven against real ffmpeg + scenedetect + opencv output.

Also closes the Registry/Pipeline wiring question that recurred every
sprint since it was first raised: six sprints with zero real callers
needing runtime provider selection is itself the answer — closed as
unnecessary, decided and recorded rather than silently dropped."

# ---------------------------------------------------------------------
# 11. Cross-builder entity merge
# ---------------------------------------------------------------------
add \
  sceneforge/knowledge/scene_merge_builder.py \
  tests/knowledge/test_scene_merge_builder.py \
  tests/knowledge/test_scene_merge_integration.py \
  docs/adr/0018-scene-merge-builder.md

commit_if_staged "knowledge: cross-builder entity merge — SceneMergeBuilder (ADR-0018)

SceneGroupingBuilder and SceneFaceBuilder each produced a separate
SCENE entity for the same logical scene, with nothing merging them.
SceneMergeBuilder combines them by reusing RelationshipBuilder's
existing Entity -> Entity shape (originally built for scene ordering)
rather than inventing a new persistence concept — the third time
checking an existing shape against a new need found it already
covered it. Each source builder's metadata is namespaced by builder
name to prevent silent field collisions from a future third builder."

# ---------------------------------------------------------------------
# 12. Cross-video query spike
# ---------------------------------------------------------------------
add \
  tests/knowledge/test_cross_video_query_spike.py \
  docs/adr/0019-cross-video-query-spike.md

commit_if_staged "knowledge: cross-video aggregation measured at scale, fourth confirmation (ADR-0019)

Deliberately different question from ADR-0014 (targeted lookup): a
full-library aggregation with no shortcut, ranking every movie in a
400-movie synthetic library by detected face count. 23,600 entities,
1,600 real FileEntityStore keys. Result: 0.391s. Fourth consecutive
real, differently-shaped measurement finding the existing Entity/
EntityStore design sufficient — used as the signal to stop spiking
this question and pivot to building a real Application next."

# ---------------------------------------------------------------------
# 13. Final sweep: everything else (docs, tracking files, examples,
#     remaining spec/architecture edits, pyproject.toml extras)
# ---------------------------------------------------------------------
git add -A

commit_if_staged "docs: sync project tracking, specs, guides, and examples through Sprint 11

Catch-all for files edited across many sprints in this session that
can't be split into per-sprint diffs without real intermediate
snapshots:

- README.md, CHANGELOG.md, SUMMARY.md, ARCHITECT_REVIEW.md,
  .ai/PROJECT_STATE.md, .ai/NEXT_TASK.md, .ai/ENGINEERING_DECISIONS.md,
  .ai/PROJECT.md — updated at the end of every sprint to reflect
  current state.
- docs/philosophy/VISION.md (new) replaces four overlapping documents
  (MANIFESTO.md, NORTH_STAR.md, CORE_PRINCIPLES.md,
  TEN_COMMANDMENTS.md — deleted) that restated the same handful of
  ideas four different ways.
- docs/NAMING_CONVENTIONS.md, docs/STYLE_GUIDE.md — filled in from
  empty (an empty spec is worse than none).
- docs/GLOSSARY.md, docs/COMPATIBILITY_POLICY.md,
  docs/architecture/LAYERS.md, docs/architecture/OVERVIEW.md,
  docs/architecture/DOMAIN_MODEL.md, docs/specifications/*.md —
  corrected stale/fictional content (fields and file paths that never
  matched the real code) and documented each ADR's findings.
- docs/guides/ADDING_A_PROVIDER.md (new) — practical checklist for
  the next provider, using every real provider shipped this session
  as a worked example.
- CONTRIBUTING.md — fixed a dangling reference to a nonexistent
  .ai/START_HERE.md.
- examples/core/registry_basic.py — was genuinely broken (referenced
  undefined classes, no imports, could never run); replaced with real
  working code.
- examples/end_to_end/analyze_video.py — grew across the session into
  the full real pipeline: load -> enrich -> extract frames -> detect
  scenes -> detect faces -> build knowledge -> sequence -> merge, all
  cached, re-run and verified against real video at every step.
- pyproject.toml — scenedetect/whisper/opencv optional extras, mypy
  overrides for untyped third-party stubs, dropped stale Python 3.10
  classifier."

echo ""
echo "Done. Review with: git log --oneline"
echo "Branch: $BRANCH"