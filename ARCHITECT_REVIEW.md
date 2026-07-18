# Chief Architect Review

## History

This file originally recorded a first review pass (surface-level:
remove dead code, replace bare `ValueError`s, add CI, kill wildcard
imports). Those were real improvements but didn't touch the
architecture itself — `Pipeline` still didn't do what its own ADR
claimed, capability data lived in a mutable global, nothing persisted,
and there was no real (non-stub) Provider anywhere in the codebase.
This entry records the pass that fixed those.

## What was actually broken

1. **`Pipeline` didn't do what ADR-0003 said it did.** It validated
   capabilities and called `provider.run()` unguarded — no timing, no
   error wrapping, no use of the already-defined `ProcessingContext`.
2. **Capability data was a global mutable dict** (`_CAPABILITY_MEDIA_MAP`)
   plus a class-level "have I registered yet" flag on `Pipeline` —
   hidden shared state, directly contradicting the project's own "no
   hidden state" principle.
3. **Nothing persisted.** The North Star ("a movie is analyzed once,
   reused forever") had no storage layer anywhere. Every `Pipeline.run()`
   produced artifacts that vanished when the process exited.
4. **No concurrency story**, despite the real target workload
   (per-scene, GPU-bound provider calls) needing one.
5. **`Media` is immutable but loaders only produce placeholder
   technical metadata** (`duration=0.0`), and there was no documented
   mechanism for turning that into authoritative metadata.
6. **`provider_protocol.Provider` only declared `run()`**, while
   `Pipeline` actually depended on `.name`/`.capabilities` too — a
   `run()`-only class satisfied the documented Protocol and would have
   crashed the moment `Pipeline` touched it.
7. **Plugins required manual registration** despite `PLUGIN_SPEC.md`
   promising installation alone was enough.
8. **Zero real (non-stub) capabilities.** `IdentityProvider`,
   `ImageInfoProvider`, `AudioInfoProvider` all produced placeholder
   data. Nothing had touched a real external tool.
9. Several docs described fields, functions, and file paths that never
   existed in the actual code (`ARTIFACT_SPEC.md`'s required-fields
   list, `NEXT_TASK.md`'s coding order, `MEDIA_SPEC.md`'s "delegated to
   Providers" claim).
10. Ceremony-to-code ratio was inverted for a solo, pre-alpha project:
    four overlapping philosophy documents, two empty spec files.

## What changed

- `Pipeline.run_detailed()` now actually times execution, retries with
  backoff, threads `ProcessingContext` for cancellation, and wraps
  provider exceptions in `ProviderExecutionError` — see ADR-0003's
  update note.
- `CapabilityRegistry` is an injectable object; `_CAPABILITY_MEDIA_MAP`
  is gone. See ADR-0007.
- `ArtifactStore` (`FileArtifactStore`, `InMemoryArtifactStore`) makes
  "analyze once, reuse forever" a literal, tested property. See
  ADR-0008.
- `AsyncProvider`/`AsyncPipeline` handle timeout, retry, and bounded
  concurrent batches (`run_many()` with per-item failure isolation).
  See ADR-0009.
- `Media.evolve()` + `MediaEnricher` protocol give an explicit,
  immutable-respecting path from placeholder to authoritative metadata.
- `provider_protocol.Provider` now declares the complete contract. See
  ADR-0006.
- `PluginRegistry.discover()` uses `importlib.metadata.entry_points()`.
- `sceneforge.contrib.ffmpeg` (`FFprobeEnricher`,
  `FFmpegFrameExtractionProvider`) is the first real, non-stub
  integration, integration-tested against an actual ffmpeg-generated
  video (`tests/contrib/test_ffmpeg_integration.py`).
- Stale docs corrected to match reality rather than aspiration;
  overlapping philosophy docs consolidated into one `VISION.md`;
  previously-empty `NAMING_CONVENTIONS.md`/`STYLE_GUIDE.md` filled in.
- 211 tests passing, `ruff check` clean, `mypy --strict` clean (54
  source files).

## Next implementation target

A second real capability — transcription, via `faster-whisper`,
wrapped as an `AsyncProvider` — is the highest-value next step: it
proves the async/timeout/retry machinery against an actually slow
model call (ffmpeg subprocess calls are fast; a real model isn't), and
it's the second data point needed before designing the Knowledge
Builder layer against real artifact shapes instead of imagined ones.
See `.ai/NEXT_TASK.md`.

## Sprint 3 update

Done: `sceneforge.contrib.scenedetect` (real, algorithmic, no model
weights) and `sceneforge.contrib.whisper` (real, model-backed,
dependency-injected per ADR-0010) both shipped, each with genuine
tests — scenedetect against real generated videos, whisper against a
structurally-compatible fake model plus a network-free shape-contract
check against the real library. `examples/end_to_end/analyze_video.py`
now runs two of the three real providers against an actual video and
was executed, not just written, during this pass.

Three real providers now cover all three provider shapes this
framework needs to support (subprocess, algorithmic, model-backed).
The next honest step is the Knowledge Builder layer — see
`.ai/NEXT_TASK.md`'s current objective — and *not* a fourth provider
for its own sake; per `docs/philosophy/VISION.md` principle 7, three
real data points is enough to design the next layer against, and
adding a fourth provider before doing so would be exactly the kind of
premature layering this project corrected away from in Sprint 2.

## Sprint 4 update

Done: `sceneforge.knowledge` — `Entity`, `KnowledgeBuilder`, and the
first real implementation, `SceneGroupingBuilder`. Scoped deliberately
narrow (ADR-0011): group frames and transcript segments into detected
scenes, nothing more ambitious yet. Proven against genuinely produced
artifacts (real ffmpeg + real scenedetect + fake-model whisper) in
`tests/knowledge/test_scene_grouping_integration.py`, not just
hand-built test fixtures — the distinction matters, since a Knowledge
Builder designed against artifacts you constructed yourself can hide
assumptions that don't survive contact with what a real Provider
actually produces (timestamps that don't land on round numbers, empty
transcript segments, frames right at a scene boundary). This test
would have caught it if the design hadn't held up. It did.

Also fixed in this pass, unrelated to the Knowledge layer but found
while touching adjacent examples: `examples/core/registry_basic.py`
was completely broken — no imports, three undefined class names. It's
a small thing, but it's exactly the kind of drift this project's
Sprint 2 corrective was about: a repository this documentation-heavy
needs its examples to actually run, or the documentation is teaching
people to write code that doesn't work.

The honest next step is *not* a second Knowledge Builder or a fourth
provider. It's answering whether `Entity` persistence extends
`ArtifactStore` or needs its own shape — an open question right now,
and the kind of question that's cheap to answer with a real spike and
expensive to get wrong by designing around in the abstract. See
`.ai/NEXT_TASK.md`.

## Sprint 5 update

Resolved: Entity persistence needed its own shape, and the only way to
know that for sure was to build both candidates. I built a shared
`Store[T]` generic first — it worked syntactically — then hit two real
differences once I tried to make it fit both `Artifact` and `Entity`
honestly: the field names that carry the same *meaning*
(`Artifact.provider` vs `Entity.builder`) are named differently on
purpose, and the natural cache-key shape genuinely differs (one media
object for Artifacts; a whole batch of artifact ids for Entities,
because `SceneGroupingBuilder` processes many media objects in one
call). Neither difference is cosmetic. `EntityStore` is now a separate
type, ADR-0012 has the full comparison, and the whole thing is proven
by `examples/end_to_end/analyze_video.py` actually caching all three
layers and checking the second run's entities are *value-equal* to
the first, not just flagged as cached.

This is the second time in this project's history (after ADR-0011)
that "spike it for real, then decide" caught something a design
document would have had to guess at. Worth noting as a pattern for
Sprint 6's relationship question, not just a one-off.

Next: represent a relationship between two entities — scene ordering
is the smallest real case — using what already exists, before adding
anything new for Layer 5. See `.ai/NEXT_TASK.md`.

## Sprint 6 update

Done: `RelationshipBuilder` + `SceneSequenceBuilder`. The
representation question resolved the way ADR-0011/0012 predicted it
would — `Entity` already had what a relationship needs (`parents` for
the two endpoints, `metadata` for what the relationship means). What I
didn't predict going in, and only found by building it: the *builder*
Protocol couldn't be `KnowledgeBuilder` reused, because
`KnowledgeBuilder.build()` is typed for Artifact input and a
relationship builder's input is Entities — the output of an earlier
stage. That's a real architectural fact about this layer, not a
convenience decision, and it changes how Layer 4 should be described
going forward: two stages, not one. `docs/architecture/LAYERS.md` says
so now.

Proven against a real three-scene video, not a toy two-scene one this
time — `test_scene_sequence_from_real_three_scene_video` confirms
`scenedetect` found exactly three cuts and `SceneSequenceBuilder`
correctly ordered them (0→1, 1→2), and that persisting a
`RELATIONSHIP`-kind entity through `EntityStore` needed zero code
changes, which is exactly the kind of validation a second real use is
supposed to provide for a design that was itself built on a spike.

Deliberately left open, on purpose, not by oversight: everything so
far queries relationships by holding a small list in memory and
filtering in Python. That's honest at "one movie, three scenes" and
untested at any real scale. Sprint 7 is that spike — see
`.ai/NEXT_TASK.md`. No graph library gets added until that spike
either needs one or doesn't.

## Sprint 7 update

Measured. 300 synthetic movies, 20 scenes each, 11,700 entities, 600
real `FileEntityStore` keys on real disk — `find_related()` for a
scene deliberately buried in the middle of the dataset: 0.125 seconds.

The more interesting finding came before the measurement, not from it:
`EntityStore` had no way to enumerate what it contained. Every method
required already knowing the key. That's not a performance problem,
it's a missing capability — you cannot query a store you cannot list.
`keys()` didn't need to be fast or clever; it needed to exist, and it
didn't, and nobody had noticed because nothing had tried to query
across more than one known key before. That's exactly the kind of gap
this project's whole method — build the real thing, don't design it on
paper — exists to catch.

With `keys()` in place, the actual performance question had a clean
answer: no, nothing new is needed yet. A linear scan over real JSON
files on disk, at a scale bigger than anything this project has
touched a movie library at, comes in well under the time it takes to
read this sentence. Building an index or reaching for a graph database
before that measurement would have been solving an imagined problem;
after it, doing so would just be premature.

This closes out the run of foundational Knowledge-layer questions that
started with ADR-0011. Every item on the "before Layer 5" checklist in
`.ai/NEXT_TASK.md` is now checked with a real implementation or a real
number. Sprint 8 is the first sprint since Sprint 3 that can honestly
say the blocker isn't an open design question — it's capability
breadth. There is still exactly one real Knowledge Builder, because
there is still exactly one domain (video/scene structure) with real
providers behind it. The image domain (`CAPTION`, `FACE_DETECTION`)
has been a registered-but-unimplemented capability since Sprint 3, and
every sprint since has correctly identified it as blocking a second
Knowledge Builder and correctly chosen to resolve a foundational
question first instead. That trade-off is used up now. Sprint 8 is the
provider.

## Sprint 8 update

Shipped `OpenCVFaceDetectionProvider`, and immediately learned
something the ADR-0010 pattern didn't predict: not every model-backed
provider needs dependency injection. Whisper needs it because
constructing a real model downloads weights from a network this
sandbox can't reach. OpenCV's Haar cascade weights ship *inside* the
package — `pip install opencv-python-headless` and the model already
exists on disk, no separate step. I checked this before defaulting to
the injection pattern a second time, and it mattered: the provider is
simpler for not carrying ceremony it doesn't need. That distinction is
now in `docs/guides/ADDING_A_PROVIDER.md`'s decision table so the next
provider author checks it too instead of reaching for injection by
habit.

Also found, the same way `EntityStore.keys()` got found in Sprint 7 —
by doing the adjacent real work and noticing the gap, not by
reviewing: `ImageMedia` has had placeholder `width=0, height=0` since
the very first sprint, and nothing had ever enriched it.
`OpenCVImageEnricher` fixes it. Three sprints of building real video
providers and nobody had touched the image side until an image
provider needed it.

What I did not do, on purpose: force the second Knowledge Builder into
this same pass just to close out Sprint 8's stated objective cleanly.
A detected face's `media_id` belongs to a derived still-frame image,
not the source video — linking it back to the scene that frame came
from is a real question, not a mechanical one, and every other
Knowledge-layer decision in this project (ADR-0011 through 0014) got a
dedicated spike before becoming permanent. Doing this one differently
just to finish a checklist item would have been the exact shortcut
this project's whole method exists to avoid. Sprint 9 is that spike,
done right instead of done fast. See `.ai/NEXT_TASK.md`.

## Sprint 9 update

The spike found a smaller answer than the question anticipated. I went
in expecting to need a third builder Protocol shape — something that
takes both already-built `SceneEntity` objects (to know which frames
belong to which scene) and raw `FaceDetectionArtifact`s. I built
toward that for a bit before noticing the actual fix was one layer
down: teach `OpenCVFaceDetectionProvider` to carry forward the frame
path it already knew (`media.metadata["source"]`, which is literally
the same file `FrameExtractionArtifact.frame_path` points at), and
`SceneFaceBuilder` never needs pre-built Entities at all — it's a
plain `KnowledgeBuilder`, correlating two Artifact types by matching
file paths, the same shape `SceneGroupingBuilder` already was. No new
Protocol. The question that looked architectural was actually a
missing field.

Proven for real: real ffmpeg frames, real scenedetect cuts, real
OpenCV calls against each frame as its own image, correctly attributed
to the right scene with zero manual relinking. Zero faces found, as
expected — no real photo available here — but the wiring is real, and
the test would have caught a wrong path match immediately if the
correlation were broken.

Also closed, properly rather than by continued silence: the
Registry/Pipeline RFC that's shown up in this file every sprint since
Sprint 3. Six sprints of building real providers, real builders, real
examples, and not one of them ever needed to select a provider by
capability at runtime instead of importing it directly. That's not
"we haven't gotten to it" anymore — it's evidence. ADR-0017 writes
down that the answer is "not yet, and here's what would change it,"
so a future sprint reopens it with a reason instead of finding a stale
checkbox and wondering whether anyone decided anything.

This is the first sprint with no carried-over foundational question at
all. Sprint 10 is the first real chance to look at Layer 5 with two
actual Knowledge Builders — from two different capability domains — to
design against, instead of one, or none. What it found waiting there
immediately: `SceneGroupingBuilder` and `SceneFaceBuilder` each
produce their own `EntityKind.SCENE` entity for the same logical scene
on the same video, and nothing merges them. Whether that's a real
problem or just how querying works now is Sprint 10's spike. See
`.ai/NEXT_TASK.md`.

## Sprint 10 update

Went in thinking this one would finally need something new — a real
merge concept, maybe a new `Entity` variant, maybe a reason to touch
`EntityStore`. It didn't. `RelationshipBuilder` already had the right
shape (`Entity -> Entity`); `SceneMergeBuilder` is that Protocol used
for a relationship type it wasn't originally written for ("these
describe the same thing" instead of "these are ordered"), and nothing
about the Protocol cared which. Namespacing each source builder's
metadata by its own name closed off the one real risk I could see
(two builders someday using the same field name for different things)
without needing to know in advance what those future builders would be.

Proven against real merged output from two independently-built,
independently-run pipelines: `SceneGroupingBuilder`'s dialogue entity
and `SceneFaceBuilder`'s face-count entity for the same real detected
scene agree exactly on `start_seconds`/`end_seconds` — not because
anything forced them to, but because both derived those numbers from
the same real `SceneCutArtifact`. That agreement is the actual
evidence the `(media_id, scene_index)` correlation key means what I
assumed it meant.

Three for three now: ADR-0011 checked whether a wider Knowledge
Builder ambition needed to be built before proving the narrow case
first (it didn't — narrow first was right). ADR-0016 checked whether
cross-domain correlation needed a new builder Protocol (it didn't — an
existing Artifact field, once carried forward, was enough). This one
checked whether cross-builder merging needed a new concept (it
didn't). That's not proof the pattern always holds — it's three data
points, and Sprint 11 deliberately picks a question shaped differently
from the last three (cross-video scale, not cross-builder or
cross-domain correlation within one video) specifically so a fourth
"yes, existing shapes cover it" result would mean something, instead
of just repeating a question similar enough to already know the
answer. See `.ai/NEXT_TASK.md`.

## Sprint 11 update

Fourth for four. I built a genuinely different kind of query this
time — not "find everything connected to this one thing I already
know about" (`find_related()`, ADR-0014), but "read the entire library
and rank it," a question with no shortcut, no known starting point,
and no way to answer it without touching every stored entity. At
400 movies and 23,600 entities, that took 0.391 seconds using nothing
but `iter_all_entities()` and a Python dict.

I want to be honest about what four-for-four does and doesn't mean.
It doesn't mean this pattern will hold forever — it means four real,
differently-shaped questions, asked in good faith with real
measurements, all came back the same way. That's enough to stop asking
a fifth version of "does Layer 5 need something new" and start asking
a different question entirely, because at this point another spike on
the same theme would itself become the thing this project's method
exists to prevent: building (or in this case, re-verifying) ahead of
any actual need.

So Sprint 12 changes what kind of work this is. Every sprint since
Sprint 2 has been infrastructure — real, tested, measured
infrastructure, and I stand behind all of it, but infrastructure
nonetheless. `docs/philosophy/VISION.md`'s own definition of success
was never "the layers exist and are well-tested." It was: someone runs
a real movie through this once, then builds real things from that
analysis. Nothing has built one of those things yet. That's Sprint
12 — not because the infrastructure work was wrong to do first, but
because it's now been proven enough times that doing a fifth round of
it instead of the actual application would be avoiding the harder,
more honest question of whether any of this is actually useful for
what it was for. See `.ai/NEXT_TASK.md`.
