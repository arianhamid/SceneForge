# ADR 0015: Face Detection Ships Real, No Injection Needed — and Closes a Second Enrichment Gap

## Status

Accepted

## Context

`.ai/NEXT_TASK.md`'s Sprint 8 objective: `CAPTION`/`OCR`/
`FACE_DETECTION`/`OBJECT_DETECTION` have been registered capabilities
with zero real implementations since Sprint 3, blocking a second
Knowledge Builder for five sprints. The dependency-injection pattern
from ADR-0010 (`WhisperTranscribeProvider`) exists for providers that
need downloaded model weights. Before defaulting to that pattern
again, it was worth checking whether this specific capability actually
needs it.

## Decision

`OpenCVFaceDetectionProvider` uses OpenCV's bundled Haar cascade
classifier (`cv2.data.haarcascades`) — trained weights that ship
*inside* the `opencv-python`/`opencv-python-headless` package itself,
not downloaded separately. This means face detection doesn't need
ADR-0010's injection pattern at all: it's the same shape as
`sceneforge.contrib.scenedetect` (real algorithm, no external network
dependency), just for a different capability and media domain (image,
not video).

Building this also surfaced a second real gap, found the same way
ADR-0014's `EntityStore.keys()` gap was found — by trying the real
task, not by review: `ImageMedia` has had placeholder `width=0,
height=0` since Sprint 1, and unlike `VideoMedia` (fixed by
`FFprobeEnricher` in Sprint 2), nothing had ever enriched it.
`OpenCVImageEnricher` closes that gap the same way, for the same
reason, three sprints later than it should have been noticed.

**Honesty about test coverage**: this environment has no real
photograph of a face and no network access to fetch one. Tests prove
the real mechanics (a real bundled cascade file, real OpenCV decoding,
correct artifact shaping, correct error handling on bad input) and the
negative path with certainty (solid-color images reliably produce zero
detections — verified manually during development that even a
hand-drawn synthetic face does not trigger a real Haar cascade, which
needs actual photographic gradients). The "detects a real face in a
real photo" claim is real production code, not a stub, but is
unverified in this sandbox — the same caveat
`docs/adr/0010-dependency-injected-model-providers.md` already
established for `WhisperTranscribeProvider`'s real model weights.

## Consequences

- `sceneforge.contrib` now spans two capability domains (video/audio,
  and image) with a fourth real provider, and the "does this need
  dependency injection" question from ADR-0010 has a genuine
  counter-example: not every model-backed capability needs it — only
  the ones whose weights aren't bundled with their library. Worth
  adding to `docs/guides/ADDING_A_PROVIDER.md`'s decision table.
- `ImageMedia` now has a real enrichment path
  (`OpenCVImageEnricher`), matching `VideoMedia`'s. `AudioMedia` still
  has none — `AudioInfoProvider` (Sprint 1, stub) never got a real
  successor, unlike `ImageInfoProvider`'s Sprint 3 vintage placeholder
  now being genuinely superseded here for the width/height fields
  specifically (not sample_rate/channels, which remain unenriched).
- The second Knowledge Builder this was meant to unblock is **not**
  built in this pass. Correlating a `FaceDetectionArtifact` (whose
  `media_id` belongs to a single still-frame `ImageMedia`, extracted
  from a video) back to the `SceneEntity` that frame belongs to is a
  real, nontrivial linking question — the same shape of problem
  `tests/knowledge/test_scene_grouping_integration.py` solved for
  transcripts via `dataclasses.replace(segment, media_id=media.id)`,
  but for frames pulled from `FrameExtractionArtifact.frame_path`
  rather than a single derived `AudioMedia`. It deserves its own spike
  rather than being rushed alongside this provider. See
  `.ai/NEXT_TASK.md`.

## Alternatives Considered

1. **Use a DNN-based face detector (e.g. OpenCV's `dnn` module with a
   Caffe/TensorFlow model) instead of Haar cascades**, for better
   accuracy. Rejected for this pass: DNN face detectors typically
   require downloading a separate `.caffemodel`/`.pb` weights file, not
   bundled with the package — reintroducing the network dependency
   Haar cascades avoid. A DNN-backed provider is a reasonable future
   addition using ADR-0010's injection pattern once accuracy actually
   matters for a real use case, not before.
2. **Force the second Knowledge Builder into this same session** to
   fully close Sprint 8's stated objective. Rejected: the media_id
   linking question is real enough to deserve being solved
   deliberately, not bolted on to avoid leaving a checkbox unchecked —
   consistent with every prior ADR in this series treating an honest
   "not yet, and here's exactly why" as better than a rushed answer.
