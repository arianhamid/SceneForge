# ADR 0022: Real OCR Provider — Second Confirmation of Cross-Domain Correlation, Still Evidence Not Facts

## Status

Accepted

## Context

ADR-0021 named the actual blocker for the Understanding Ladder's
"Facts" rung: a provider producing something above raw detection.
`Capability.OCR` had been a registered capability with zero real
implementation since Sprint 3. Checking bundled-vs-downloaded weights
first, per the lesson ADR-0015 learned the hard way: `tesseract-ocr`
ships `eng.traineddata` as part of its system package, installed via
`apt`, with no network access needed at runtime — the same "bundled,
not fetched" shape as OpenCV's Haar cascades, not
`WhisperTranscribeProvider`'s downloaded-weights shape.

Unlike `WhisperTranscribeProvider` (real weights need network access
this environment doesn't have) and `OpenCVFaceDetectionProvider` (no
real face photo available here), this provider's positive-detection
claim is **genuinely verified in this environment**: real text
rendered with a bundled system font into a real image, and later
burned into a real video via `ffmpeg`'s `drawtext` filter, read back
correctly by the real Tesseract binary.

## Decision

`TesseractOCRProvider` (`Capability.OCR`) ships as a real, no-injection
provider, mirroring `OpenCVFaceDetectionProvider`'s shape exactly.
`OCRTextArtifact` carries `source_frame_path` (auto-populated from the
decoded image's own metadata), the same field `FaceDetectionArtifact`
uses for cross-domain correlation (ADR-0016).

`SceneTextBuilder` (`KnowledgeBuilder`) groups OCR text into scenes by
matching `source_frame_path` against `FrameExtractionArtifact.frame_path`
— the exact same correlation pattern as `SceneFaceBuilder`, now
confirmed working for a **second** real capability, not just the one
it was originally built for. Proven against a real video: black text
burned into a white first scene, white text into a black second scene,
`scenedetect` finding the real cut, Tesseract reading each scene's
text back correctly and attributing it to the right scene, not the
other one (`tests/knowledge/test_scene_text_integration.py`).

**Explicitly not claimed: this does not reach the "Facts" rung.**
Grouping recognized text by scene is still the Evidence layer,
organized — the same rung `SceneGroupingBuilder` and `SceneFaceBuilder`
already occupy. A sign reading "POLICE" becoming the Fact "this
location is a police station" needs a semantic interpretation step
`SceneTextBuilder` does not attempt and was not built to attempt. This
ADR ships real OCR and confirms a second cross-domain builder; it does
not close ADR-0021's Facts entry in `DOMAIN_MODEL.md`, which still
correctly says "Not built."

Also fixed in this pass: `ArtifactCategory` (added in an earlier pass
with zero real consumers — every artifact silently defaulted to
`METADATA`) now has real values set on all real artifact types,
including `OCRTextArtifact` → `RECOGNITION`.

## Consequences

- Five real providers now exist, across three capability domains
  (video/audio: `ffmpeg`, `scenedetect`, `whisper`; image:
  `opencv`, `tesseract`).
- `SceneFaceBuilder`'s correlation pattern (ADR-0016) is now confirmed
  twice, not once — real evidence it's a reusable pattern for the next
  per-frame capability (a captioning provider, when it ships), not a
  one-off that happened to work for faces.
- `docs/architecture/DOMAIN_MODEL.md`'s Understanding Ladder entry for
  "Evidence" gains OCR as a real source; "Facts" remains honestly
  marked "Not built," with its trigger condition unchanged
  (`CAPTION`/`OBJECT_DETECTION`, still not shipped).
- The next real step toward Facts is still a captioning provider —
  OCR text is evidence *about* on-screen text, not an interpretation
  of what a scene depicts. Both are needed; only one is closer to
  "Facts" in the vision document's stricter sense.

## Alternatives Considered

1. **Treat recognized text as a Fact directly** ("POLICE" sign →
   "this is a police station"). Rejected: that's an interpretation
   step, not a detection — conflating them would mean shipping a
   provider that quietly claims semantic understanding it doesn't
   have, which `docs/architecture/DOMAIN_MODEL.md`'s own ladder
   explicitly warns against ("Facts... still objective," not
   inferred).
2. **Wait for a captioning provider and build both at once.** Rejected
   — OCR was real, bundled, and verifiable today; no reason to hold it
   back for a provider that still needs its own dependency-injection
   design work.
