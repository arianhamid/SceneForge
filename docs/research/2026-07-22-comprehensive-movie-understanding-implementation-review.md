# Comprehensive Movie Understanding: Implementation Review

- **Review date:** 2026-07-22
- **Repository revision reviewed:** `36860dd`
- **Primary research document:**
  [Comprehensive Movie Understanding Architecture](./2026-07-21-comprehensive-movie-understanding-architecture.md)
- **Review scope:** current source code, tests, project-state documents, architecture,
  specifications, recent ADRs, the English and Persian research documents, and the
  research document's principal external claims.

## Executive verdict

The research document is a strong product and epistemic north star, but it is not
yet an implementation-ready architecture.

Its most valuable decisions are:

- separating movie evidence, external-source claims, interpretation, and forecasts;
- modeling both presentation time and story time;
- making confidence, coverage, missingness, and disagreement explicit;
- retaining source attribution and rights information;
- requiring evidence-oriented release gates;
- keeping the system model-neutral;
- avoiding a premature graph-database migration.

The current repository is a coherent pre-alpha extraction and scene-knowledge
framework. It is not yet a durable, edition-aware, reproducible narrative evidence
platform. The most serious risk is not choosing an imperfect captioning or object
model. It is allowing weak identity, cache, provenance, anchoring, and revision
contracts to harden underneath all future knowledge and intelligence layers.

The proposed caption/object milestone remains reasonable, but a small correctness
phase must precede it. Otherwise later results may be fluent and impressive while
being impossible to reproduce, trace to durable evidence, compare across runs, or
scope to the correct movie edition.

## Current implementation baseline

Repository truth, confirmed against source and tests, currently includes:

- immutable top-level `Media`, `Artifact`, and `Entity` dataclasses;
- injectable capability state;
- file-backed artifact and entity caches;
- real integrations for FFmpeg frame extraction, PySceneDetect, Whisper, OpenCV
  face detection, Tesseract OCR, and media hashing;
- scene grouping, scene-face, scene-text, scene-sequence, and scene-merge builders;
- a simple scene-summary application;
- strict typing, linting, architecture tests, and a healthy unit-test suite.

It does not currently include a first-class Fact model, events, persistent
characters, state timelines, causal reasoning, source claims, interpretations,
forecasts, a durable evidence repository, or a comprehensive analysis-run
orchestrator. This agrees broadly with
[PROJECT_STATE.md](../../.ai/PROJECT_STATE.md) and
[NEXT_TASK.md](../../.ai/NEXT_TASK.md), although some documentation overstates the
completeness of provenance, immutability, runtime decoding, and plugin support.

## Severity-ranked findings

### Critical 1: cache identity is neither content identity nor execution identity

`Media.id` is a new random UUID for each object
([media/base.py](../../sceneforge/media/base.py#L24)). Loaders therefore create a new
identity every time the same file is loaded
([video_loader.py](../../sceneforge/media/video_loader.py#L51)).

The cache key hashes only:

- media name;
- random media UUID;
- provider name;
- provider version.

See [core/storage.py](../../sceneforge/core/storage.py#L70).

This creates two opposite correctness failures:

1. Reloading the same unchanged file produces a different key and a false cache
   miss.
2. Running two configurations of the same provider against one `Media` object
   produces the same key and can return the wrong cached artifact.

Behavior-changing configuration currently omitted from identity includes:

- FFmpeg frame count and output behavior
  ([frame_extraction_provider.py](../../sceneforge/contrib/ffmpeg/frame_extraction_provider.py#L55));
- SceneDetect threshold and minimum scene length
  ([scenedetect/provider.py](../../sceneforge/contrib/scenedetect/provider.py#L46));
- Whisper model identity and transcription keyword arguments
  ([whisper/provider.py](../../sceneforge/contrib/whisper/provider.py#L93));
- OCR language and confidence threshold
  ([ocr_provider.py](../../sceneforge/contrib/tesseract/ocr_provider.py#L50)).

`MediaHashProvider` computes useful content information
([media_hash/provider.py](../../sceneforge/contrib/media_hash/provider.py#L44)), but
its result is not integrated into media or cache identity.

#### Required correction

Introduce two separate identities:

- **Content identity:** hash of the exact bytes or normalized local asset.
- **Work/edition identity:** the logical movie and specific cut/release, which may
  be unresolved until user input or external catalog matching is available.

Also introduce a canonical execution fingerprint containing:

- provider implementation and schema versions;
- model ID, revision, and preferably weights hash;
- prompt/template version;
- sampling and preprocessing configuration;
- inference parameters;
- relevant external tool and library versions.

Cache identity should derive from content/edition identity plus the execution
fingerprint. The complete fingerprint must also be persisted in the result and run
manifest.

### Critical 2: provenance is defined but not usable

`Provenance` exists as a nested dataclass
([knowledge/entity.py](../../sceneforge/knowledge/entity.py#L28)), but production
builders do not populate it. The entity serializer handles UUIDs, datetimes, enums,
lists/tuples, and mappings, but not the `Provenance` dataclass
([knowledge/storage.py](../../sceneforge/knowledge/storage.py#L70)).

A direct persistence check produced:

```text
TypeError: Object of type Provenance is not JSON serializable
```

The existing unit test constructs provenance only in memory
([test_entity.py](../../tests/knowledge/test_entity.py#L43)). It does not persist and
reload it.

This makes statements that provenance is already a reliable shipped foundation too
strong. Provenance must be serialization-tested, round-trip-tested, and populated by
real builders before Facts or reasoning depend on it.

At minimum, Fact-and-higher outputs should record:

- producer/builder identity and version;
- execution fingerprint;
- analysis-run ID;
- source evidence IDs;
- creation and assessment times;
- uncertainty dimensions;
- superseded revision, if any.

### Critical 3: the system cannot resolve a conclusion back to durable evidence

Base `Artifact` does not require source media, occurrence interval, stream, spatial
anchor, model/configuration fingerprint, schema version, or run identity
([core/artifact.py](../../sceneforge/core/artifact.py#L61)).

`Entity.parents` is an untyped tuple of UUIDs. Depending on context, those UUIDs can
mean source Artifacts, source Entities, or relationship endpoints. `ArtifactStore`
supports cache-key operations but no lookup by artifact ID, media, stream, or time
([core/storage.py](../../sceneforge/core/storage.py#L137)). An application therefore
cannot reliably expand a conclusion into its source evidence.

This directly blocks the research document's "show evidence" requirement.

#### Required correction

Introduce a small typed contract such as:

- `EvidenceAnchor`: edition, stream, presentation interval or point, frame/PTS,
  optional spatial region, and durable asset reference;
- `EvidenceLink`: source ID, target ID, and relation such as `supports`, `opposes`,
  `contextualizes`, or `derived_from`;
- artifact lookup by ID and indexed lookup by edition/media/time.

This does not require a graph database. An indexed repository or SQLite-backed spike
is sufficient.

### Critical 4: path strings are being used as identity and lineage

Face and OCR observations retain `source_frame_path`
([face_detection_artifact.py](../../sceneforge/contrib/opencv/face_detection_artifact.py#L23),
[ocr_artifact.py](../../sceneforge/contrib/tesseract/ocr_artifact.py#L30)). Scene
builders join those observations to frame-extraction results using exact path-string
equality
([scene_face_builder.py](../../sceneforge/knowledge/scene_face_builder.py#L65),
[scene_text_builder.py](../../sceneforge/knowledge/scene_text_builder.py#L63)).

Frame extraction defaults to a new temporary directory
([frame_extraction_provider.py](../../sceneforge/contrib/ffmpeg/frame_extraction_provider.py#L94)).
The JSON cache can therefore outlive the image pixels that supposedly support it.

Every derived image or crop needs first-class lineage:

- source edition and stream ID;
- source frame artifact ID;
- verified PTS/timebase or interval;
- spatial transformation/crop;
- durable content-addressed asset reference.

A filesystem path may remain a replaceable locator, but it must not be treated as
identity or evidence.

### Critical 5: Phase 1 has no defensible Fact contract

`EntityKind` has no `FACT`, `OBJECT`, `STATE`, `ASSERTION`, or `SHOT`
([knowledge/entity.py](../../sceneforge/knowledge/entity.py#L37)). The research's
atomic assertion record is explicitly conceptual, while the concrete ADR for
assertions and evidence links is deferred until after the first Fact milestone.

That ordering should be reversed. Otherwise the first Fact will likely become an
untyped metadata dictionary that future stages cannot safely query or revise.

A free-form caption is not automatically an objective Fact. A caption may:

- contain several propositions;
- omit short or subtle actions;
- hallucinate identity or intent;
- merge observation and interpretation;
- describe a transition that one sampled frame cannot establish.

For example, "a door opens" requires before/after temporal evidence. One frame can
support "a door is visible" or possibly "the door appears open," not the transition
itself.

#### Recommended first Fact

Start with a deliberately constrained proposition such as:

> Category X is visible in region R of source frame F at presentation time T.

The experimental record should include:

- a stable logical key and separate immutable revision ID;
- a constrained proposition or subject/predicate/object shape;
- presentation anchor;
- typed evidence links;
- acquisition confidence separate from assertion confidence;
- provider, model, schema, and execution versions;
- abstention and supersession semantics.

Do not declare the entire Facts rung implemented merely because a vision-language
model generated fluent prose.

### High 6: exact edition and common-clock support are overstated

`VideoMedia` stores only basic video properties
([media/video.py](../../sceneforge/media/video.py#L15)). `FFprobeEnricher` selects
only the first video stream and keeps duration, codec, FPS, width, and height
([probe_enricher.py](../../sceneforge/contrib/ffmpeg/probe_enricher.py#L76)).

Missing information includes:

- audio, subtitle, commentary, and chapter tracks;
- language and disposition metadata;
- track timebases and offsets;
- variable-frame-rate behavior;
- edit lists and verified presentation timestamps;
- derived audio/frame lineage;
- local edition fingerprint.

Current extracted-frame timestamps represent requested seek positions rather than
a fully verified source PTS contract. Sample index is also not necessarily the
original frame number.

Local byte identity can be established without the internet. Automatically knowing
that bytes correspond to a named theatrical, director's, broadcast, or regional cut
usually cannot. That requires embedded metadata, a user assertion, or external
matching.

Complete local stream inventory and fingerprinting must move to Phase 0. External
work/edition catalog matching can remain in the external-research phase.

### High 7: immutability and evidence permanence are only shallow claims

`Artifact` and `Entity` protect only the outer metadata mapping with
`MappingProxyType`
([core/artifact.py](../../sceneforge/core/artifact.py#L77),
[knowledge/entity.py](../../sceneforge/knowledge/entity.py#L77)). Nested lists,
dictionaries, and mutable payload objects remain mutable. This was directly
reproduced by appending to a list nested in frozen entity metadata.

Real builders persist nested mutable values, including frame lists and face maps.
Both file stores also support overwrite and deletion. That is acceptable for an
evictable computation cache, but it is not append-only evidence permanence.

The architecture should distinguish:

- an evictable/rebuildable computation cache;
- durable source assets;
- append-oriented evidence and knowledge revisions;
- explicit tombstone, retention, and supersession behavior.

Use typed frozen payloads or recursive freezing where immutability is promised.

### High 8: provider interchangeability is not yet real

Knowledge builders import concrete provider-owned Artifact classes. For example,
`SceneGroupingBuilder` imports FFmpeg, PySceneDetect, and Whisper classes directly
([scene_grouping_builder.py](../../sceneforge/knowledge/scene_grouping_builder.py#L25)).
Architecture tests explicitly allow these dependencies
([test_import_rules.py](../../tests/architecture/test_import_rules.py#L32)).

A second ASR, OCR, scene detector, captioner, or object detector will not be
interchangeable merely because it advertises the same capability. It must also emit
the existing contrib-owned concrete class, or every builder must learn each provider
shape.

Introduce provider-neutral normalized artifact schemas at the Artifact boundary, or
small structural payload protocols demonstrated by at least two real providers.
Provider-specific raw output can remain alongside the normalized record when useful.

### High 9: media compatibility is modeled at the wrong level

The default capability registry reports OCR and face detection as supporting video
media
([capability_registry.py](../../sceneforge/core/capability_registry.py#L83)), while
the actual Tesseract and OpenCV providers accept only `ImageMedia`
([ocr_provider.py](../../sceneforge/contrib/tesseract/ocr_provider.py#L70),
[face_detection_provider.py](../../sceneforge/contrib/opencv/face_detection_provider.py#L83)).

This means preflight validation can succeed and provider execution can still reject
the media. Captioning will intensify the mismatch because image-only, clip-native,
and long-video-native captioners have different input contracts despite sharing a
broad capability label.

Supported media and execution requirements need to be provider-specific. The global
capability catalog can remain descriptive, but it cannot be the final compatibility
authority.

### High 10: the documented Runtime boundary is not the implemented boundary

[LAYERS.md](../architecture/LAYERS.md) says Providers request decoding through
Runtime and do not decode directly. The only decoder implementation is
`StubDecoder`
([stub_decoder.py](../../sceneforge/runtime/media_runtime/stub_decoder.py#L21)), and
runtime representations expose no useful time-addressable access methods.

Real integrations invoke FFmpeg, PySceneDetect, faster-whisper, OpenCV, or Pillow
directly. The research document repeats the intended Runtime placement as if it were
already operational.

Before adaptive sampling, record an ADR choosing one honest architecture:

1. implement a shared time-addressable decoding/sampling service injected into
   providers; or
2. formally assign decoding/extraction to provider integrations and retire the
   unused Runtime promise.

Because face, OCR, caption, object, style, and tracking stages will reuse frames, a
shared durable sampler now has real consumers and may be justified.

### High 11: cross-domain media lineage remains application glue

The scene-grouping integration manually changes transcript media IDs to the source
video ID
([test_scene_grouping_integration.py](../../tests/knowledge/test_scene_grouping_integration.py#L121)).
Face and OCR association depends on path equality. There is no first-class
relationship connecting:

- container;
- selected audio/video/subtitle stream;
- decoded frame or audio segment;
- crop or transformed derivative;
- originating edition.

Without this lineage, multimodal alignment can silently join observations from the
wrong stream, transformation, or run.

### High 12: relationship records overload several meanings

Ordinary entities use `parents` for derivation. Relationship entities use the same
field for graph endpoints
([relationship_builder.py](../../sceneforge/knowledge/relationship_builder.py#L91)).
Relationship type and direction live in free-form metadata.

This cannot cleanly express:

- typed source and target endpoints;
- valid presentation/story intervals;
- evidence support or opposition;
- derivation versus semantic relationship;
- confidence and assessment revision;
- identity merge/split and supersession.

Relationships should have explicit endpoints and typed semantics. Derivation and
evidence links should not be encoded as ordinary story-world relationships.

### High 13: the Entity store is a build cache, not yet a knowledge repository

Entity queries enumerate and deserialize JSON buckets
([knowledge/storage.py](../../sceneforge/knowledge/storage.py#L209)). There is no
canonical entity resolution, edition/run scoping, temporal or predicate index,
revision chain, transaction model, or referential integrity.

Current query benchmarks contain tens of thousands of small flat synthetic entities.
That is valid evidence for current scene-summary scale, but it does not represent
dense detections, assertions, state snapshots, evidence links, source claims, and
multi-hop report queries.

The new research use cases provide a legitimate trigger for another storage spike.
Benchmark the actual required report queries. SQLite is likely sufficient before a
graph database becomes justified.

### High 14: the current application cannot isolate a movie or canonical scene view

`SceneSummary` scans every `SCENE` in its Entity store without a media, edition,
analysis-run, or builder selector
([scene_summary.py](../../sceneforge/applications/scene_summary.py#L54)). A shared
store can therefore mix multiple movies. It can also return source, face-enriched,
text-enriched, and merged representations of the same scene.

Merged-scene metadata does not use exactly the same top-level shape expected by the
summary, so some fields fall back to defaults.

Before a comprehensive report, define:

- edition/run query scope;
- canonical record or materialized-view selection;
- revision and merge semantics;
- explicit handling of incomplete or conflicting scene representations.

### High 15: comprehensive analysis now has a real orchestration caller

`Pipeline` intentionally executes one provider against one media object
([pipeline.py](../../sceneforge/core/pipeline.py#L74)). The end-to-end example
manually assembles stages
([analyze_video.py](../../examples/end_to_end/analyze_video.py#L41)). That is
appropriate for the current framework, but insufficient for dozens of conditional
and resource-heavy stages.

The research scrutiny contract requires model versions, parameters, tracks,
sampling, skipped intervals, failures, cache status, and coverage. No phase clearly
implements the durable manifest needed to produce that information.

Keep the existing `Pipeline` stable, but add a separate application-service concept
such as `AnalysisRun` with:

- workflow and configuration fingerprint;
- typed step dependencies;
- input and output artifact-set references;
- start/end/failure/skip status;
- checkpoint and partial-rerun information;
- cache-hit state;
- interval and modality coverage;
- resource profile.

This need not become a generic workflow engine.

### High 16: cancellation and resource control are weaker than required

`Provider.run()` receives only `Media`, not `ProcessingContext`
([provider_protocol.py](../../sceneforge/core/provider_protocol.py#L51)). Cancellation
can therefore be observed between provider calls, but not necessarily during a long
model invocation.

A synchronous provider launched through the async adapter may continue executing in
its worker thread after the caller times out
([async_provider.py](../../sceneforge/core/async_provider.py#L72)). `max_concurrency`
is a call-count limit, not a VRAM, RAM, decoder, model-instance, or API-rate budget.
Injected model objects also lack a thread-safety declaration.

Long-video processing needs cooperative cancellation where supported, subprocess
termination policies, stage checkpoints, and named resource semaphores.

### High 17: plugin contracts do not cover the proposed source and intelligence lanes

The implemented `Plugin` interface exposes Providers
([plugins/plugin.py](../../sceneforge/plugins/plugin.py#L39)). The domain model talks
more broadly about plugin builders, reasoners, and applications
([DOMAIN_MODEL.md](../architecture/DOMAIN_MODEL.md)), while the plugin specification
remains provider-focused
([PLUGIN_SPEC.md](../specifications/PLUGIN_SPEC.md)). The research additionally
proposes plugin-owned source ingestors.

Serialization registries are keyed by unqualified class name, allowing collisions
between plugins. Reading an unfamiliar subclass can also fall back to a base record
and lose provider-specific fields. Plugin discovery silently suppresses some broken
imports
([plugins/registry.py](../../sceneforge/plugins/registry.py#L36)), preventing the run
manifest from explaining why a capability was unavailable.

Before external-source ingestion, define namespaced type/schema IDs and decide which
extension points are actually discoverable. Do not generalize the plugin contract
until each extension point has a real caller.

### High 18: the research's epistemic schema has internal inconsistencies

The proposed statement classes mix orthogonal concerns:

- origin or epistemic status: observation, inference, interpretation;
- semantic subject: identity, attribution, culture, causality;
- assessment state: accepted, rejected, disputed, unsafe to generalize.

The proposed verdict vocabulary does not apply consistently across all classes. A
single enum will either accumulate unrelated values or lose important distinctions.

Use separate dimensions such as:

- `ClaimType`;
- `Origin`;
- `EvidenceRole`;
- task-specific `AssessmentVerdict`;
- confidence/calibration record;
- assessor and assessment revision.

Other ordering inconsistencies include:

- Phase 3 exits with a multi-scene causal question although causality is introduced
  in Phase 5;
- character state combines physical state, possession, knowledge, belief, affect,
  goal, and intention;
- causal links are partially assigned to relationship builders even though inferred
  motive and causality belong to Intelligence;
- dual timelines arrive too late for event and state identities that already need
  them.

Separate observed/explicit causal statements from inferred causal hypotheses.
Likewise separate world state, epistemic state, affect, and goals.

### High 19: forecasting is an independent research problem

Probabilities cannot be meaningfully normalized across arbitrary natural-language
scenarios unless the outcomes are defined to be mutually exclusive and collectively
exhaustive, or the system clearly states a different probabilistic interpretation.

Historical backtesting also has a serious leakage problem: filtering retrieved web
sources by date does not remove future knowledge embedded in pretrained model
weights. Reliable evaluation needs time-appropriate models or carefully designed
baselines, fixed outcome-resolution rules, and explicit leakage analysis.

Forecasting should therefore remain an experimental application with:

- predefined resolvable events;
- resolution ontology and adjudication;
- Brier/log-score-compatible outcomes;
- calibration and abstention baselines;
- time-sliced evaluation;
- a failure mode that does not undermine the evidence and knowledge platform.

The rest of SceneForge can succeed even if calibrated forecasting does not.

### High 20: evaluation is currently structural, not semantic

The current evaluation tests establish output existence, requested counts, and broad
structural ranges. For example, scene count is accepted over a wide range
([test_evaluation.py](../../tests/integration/test_evaluation.py#L90)). A test named
`test_entity_ids_are_deterministic` does not compare entity IDs
([test_evaluation.py](../../tests/integration/test_evaluation.py#L132)).

The repository does not yet contain gold-set measurements for:

- shot/scene boundary precision and recall;
- ASR WER or OCR CER;
- face/object precision, recall, and identity switches;
- temporal grounding;
- atomic Fact precision and abstention;
- evidence-link correctness;
- citation entailment;
- interpretation quality or reviewer agreement;
- forecast calibration.

The research document lists useful metric categories, but it does not yet define:

- annotation schema and dataset card;
- licensed source media;
- sample sizes or splits;
- acceptance thresholds;
- inter-rater agreement and adjudication;
- multilingual/cultural review governance;
- regression policy;
- benchmark contamination and leakage policy.

For advanced layers, evaluation data and human review are likely to cost more than
provider integration.

### High 21: security, privacy, and rights need operational specifications

The research correctly discusses attribution, robots policies, paywalls, source
snapshots, and prompt injection. A production source ingestor also needs protection
against:

- SSRF and private-address access;
- DNS rebinding and unsafe redirects;
- oversized responses and decompression bombs;
- MIME confusion;
- malicious PDF, image, archive, and HTML parsing;
- credential or internal-data exfiltration;
- untrusted active content;
- deletion and retention propagation.

Persistent face, voice, and re-identification features additionally need rules for:

- biometric privacy and legal basis;
- consent where applicable;
- minors and sensitive subjects;
- access control;
- retention and deletion;
- sensitive-attribute inference;
- auditability and user correction.

The project also needs a policy for local copyrighted movies and retained derivative
frames, audio, embeddings, and thumbnails—not only external web sources.

Append-only technical history must be reconciled with legal deletion. Tombstones,
key destruction for encrypted assets, and redacted audit records may be necessary.

## Documentation inconsistencies

These should be corrected before the research document is treated as the canonical
implementation roadmap:

1. [OVERVIEW.md](../architecture/OVERVIEW.md) and
   [LAYERS.md](../architecture/LAYERS.md) use different layer numbering and counts.
2. [ARTIFACT_SPEC.md](../specifications/ARTIFACT_SPEC.md) says Artifacts represent
   facts, conflicting with ADR-0021 and the research's Evidence-to-Facts separation.
3. The same Artifact specification says every Artifact knows when it occurred, but
   the base Artifact only guarantees its creation time.
4. It calls mapping-proxy metadata truly immutable although nested values remain
   mutable.
5. [BUILDER_DEPENDENCIES.md](../architecture/BUILDER_DEPENDENCIES.md) omits the
   shipped `SceneTextBuilder` and visually serializes otherwise independent work.
6. [NEXT_TASK.md](../../.ai/NEXT_TASK.md) also omits `SceneTextBuilder` from parts of
   its completed summary.
7. Runtime documentation promises provider-independent decoding that has not been
   implemented.
8. Provider documentation describes providers as pure and side-effect-free despite
   integrations that invoke tools and write derived files.
9. Plugin scope differs across the domain model, plugin specification, and code.
10. Some status/readme text still refers to three providers although five feature
    providers plus media hashing are shipped.
11. Architecture import tests enforce selected dependency rules, not every
    no-exception rule stated in prose.

The documentation should clearly label each contract as one of:

- implemented and enforced;
- accepted target architecture;
- exploratory research proposal.

`LAYERS.md` should be the canonical dependency-direction document unless a new ADR
explicitly supersedes it.

## Recommended implementation sequence

### Phase 0: trustworthy identity and evidence

Before adding another model-backed capability:

1. Define content, work, edition, derived-media, and analysis-run identities.
2. Implement deterministic provider execution fingerprints.
3. Complete local container/stream/timebase inventory.
4. Add typed evidence anchors and links.
5. Repair provenance serialization and require real builders to populate it.
6. Separate computation cache from durable evidence/revision storage.
7. Add by-ID/media/time lookup and edition/run scope.
8. Introduce a small persisted analysis-run manifest.
9. Decide the honest Runtime/decoding boundary through an ADR.
10. Reconcile architecture and specification documentation with source truth.

This is foundational correctness work, not premature infrastructure.

### Phase 1: one narrow grounded Fact

1. Record an ADR for the experimental Fact, EvidenceAnchor, EvidenceLink, confidence,
   and revision contracts.
2. Choose one constrained proposition.
3. Build a small licensed gold set before choosing or tuning the model.
4. Define precision, coverage, and abstention acceptance thresholds.
5. Add one provider-neutral normalized object/caption artifact contract.
6. Implement one real provider and one Fact builder.
7. Keep free-form model prose as evidence unless it is atomized and validated.
8. Add a thin evidence/coverage viewer immediately.

### Phase 2: adaptive evidence and semantic scenes

- Preserve `SceneCutArtifact` as a visual-shot boundary for compatibility.
- Build semantic scenes as new records composed from shots and multimodal evidence.
- Use a shared or explicitly owned sampling contract.
- Persist coverage, skipped intervals, and failed modalities.
- Benchmark real report queries against the revised store.

### Phase 3: identity, events, and state

- Introduce stable logical identities plus immutable revisions.
- Add typed directional relationships and evidence links.
- Put presentation and story intervals on events from their first version.
- Represent uncertain story chronology as constraints or partial order rather than
  forcing one exact timestamp.
- Separate physical, possession, epistemic, affective, and goal state.

### Phase 4: external-source evidence

- Match local editions to external work/edition records.
- Add source ingestion only after its security and rights ADRs.
- Preserve source snapshots, retrieval time, attribution, rights, transformations,
  and quoted/paraphrased status.
- Treat external statements as source claims, not automatically as truth.
- Add namespaced extension and codec contracts only where real plugins require them.

### Phase 5 and later: reasoning and interpretation

- Keep observed/explicit causal claims separate from inferred hypotheses.
- Store competing interpretations and assessments rather than selecting one hidden
  canonical reading.
- Require human review for cultural, historical, and sensitive interpretations.
- Preserve disagreement and assessor context.
- Release a read-only evidence report incrementally instead of waiting until the
  final phase for the first real consumer.

### Separate experimental track: forecasting

Do not make completion of the evidence/knowledge architecture depend on forecasting.
Treat forecast generation, outcome resolution, leakage-resistant backtesting, and
calibration as a separate research program.

## Suggested non-negotiable gates

### Identity gate

- The same unchanged media loaded in separate processes resolves to the same content
  identity.
- Changed bytes produce a new content identity.
- Different provider/model/configuration fingerprints cannot collide.
- The full identity inputs are inspectable from persisted records.

### Evidence gate

- Every released Fact resolves to durable source evidence.
- Missing source assets are detected rather than silently ignored.
- Anchors retain edition, stream, time, and spatial context.
- Evidence can be displayed without depending on an original temporary path.

### Fact gate

- The proposition has a typed contract.
- Precision, coverage, and abstention are measured on a documented gold set.
- Caption prose is not silently promoted to atomic truth.
- Conflicting or superseding assessments remain inspectable.

### Run gate

- Provider/model/configuration versions are recorded.
- Failed and skipped stages and intervals are explicit.
- Cache hits and reruns are distinguishable.
- Coverage is computed from the manifest, not inferred from whichever outputs happen
  to exist.

### Report gate

- Every conclusion shows its epistemic class and evidence.
- Edition/run scope is explicit.
- Unknown, unsupported, disputed, and not-applicable states are distinguishable.
- Interpretation and forecast sections cannot masquerade as direct observation.

## Difficulty and feasibility assessment

### Achievable engineering work

- stable content and execution identity;
- provenance persistence;
- durable anchors and artifact lookup;
- run manifests;
- one narrow object-visibility Fact;
- early evidence viewer;
- indexed repository without a graph database.

### Substantial but tractable work

- shared/adaptive media sampling;
- semantic scene construction;
- multimodal stream alignment;
- persistent identity and tracking;
- events, state snapshots, and revision-aware queries;
- source ingestion with rights and security controls.

### Very difficult research and operations

- long-range causal reasoning;
- character beliefs, intentions, and unreliable narration;
- story-time reconstruction under flashbacks and ambiguity;
- culturally responsible interpretation across languages and communities;
- human-review workflows and disagreement governance.

### Open-ended research

- calibrated forecasts for unrestricted narrative futures;
- human-level comprehensive movie understanding;
- reliable interpretation of symbolism, motive, and cultural meaning without expert
  oversight.

For a small team, the complete vision is likely a multi-year program. The dominant
costs will probably be evaluation media, annotation, legal rights, privacy controls,
multilingual/domain experts, and temporal grounding rather than provider adapter
code.

## External-source cross-check

The research document's sources support its architectural caution, but they should
not be treated as proof that the complete automated system is feasible.

- [TemporalBench](https://arxiv.org/abs/2410.10818) reported a large gap between
  people and leading models on fine-grained temporal understanding when published.
  This supports treating long-form temporal reasoning as an unresolved problem.
- [MovieNet](https://arxiv.org/abs/2007.10937) demonstrates the usefulness of rich
  movie annotations, but also illustrates the scale of annotation and alignment
  required.
- The [W3C Web Annotation Data Model](https://www.w3.org/TR/annotation-model/)
  supports timed multimedia targets and is relevant to anchor design, but it does
  not supply SceneForge's edition, run, confidence, or revision semantics.
- The [EIDR FAQ](https://www.eidr.org/faq) confirms identifiers at work, edit, and
  specific-version levels. EIDR is an identifier system, not a universal local-file
  recognition or rich metadata oracle.
- The [C2PA explainer](https://c2pa.org/specifications/specifications/2.2/explainer/Explainer.html)
  explicitly separates provenance from truth judgments. C2PA can support source
  history, not establish that a claim is correct.
- [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html) specifies robots exclusion
  behavior but makes clear that robots rules are not authorization controls.
- Copyright exceptions remain jurisdiction- and fact-specific; see the
  [U.S. Copyright Office fair-use guidance](https://www.copyright.gov/fair-use/) and
  the [EU Digital Single Market Directive](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=uriserv%3AOJ.L_.2019.130.01.0092.01.ENG).

Additional research is advisable on multimodal hallucination and grounding,
diarization/tracking, audio-video synchronization, biometric privacy, hostile-source
ingestion, annotation disagreement, and full-length-video evaluation.

## Verification performed

Environment:

```text
Python 3.12.13
```

Commands:

```text
make check PYTHON=.venv/bin/python
.venv/bin/python -m pytest -q -rs
git diff --check HEAD^..HEAD
```

Results:

```text
ruff check: passed
ruff format --check: passed
mypy --strict: passed (83 source files)
pytest: 351 passed, 22 skipped
latest-commit whitespace check: passed
```

Skipped tests included optional real integrations unavailable in the review
environment, including PySceneDetect, OpenCV, the Tesseract executable, and
`faster_whisper`. A skipped integration test is not evidence that the integration
works.

Targeted direct checks reproduced:

1. failure to JSON-persist an Entity containing non-null `Provenance`;
2. mutation of nested metadata inside a frozen Artifact/Entity;
3. different cache keys after reloading the same logical file;
4. identical cache keys for behaviorally different provider configurations.

Relative links and footnote definitions in the English research document were also
checked. The English and Persian companion documents remain structurally parallel.

No production source code was changed during this review.

## Final recommendation

Preserve the research document as the product north star, but insert a formal
**Phase 0: Trustworthy Identity, Evidence, and Runs** before the current provider
roadmap.

After that foundation, implement one narrow, measurable Fact and an evidence viewer.
Advance only when the system can prove which edition was analyzed, which exact
configuration produced a result, what durable evidence supports it, what coverage
was missing, and how a later assessment superseded an earlier one.

That sequence gives SceneForge the best chance of becoming a trustworthy narrative
knowledge framework rather than a collection of persuasive but untraceable model
outputs.
