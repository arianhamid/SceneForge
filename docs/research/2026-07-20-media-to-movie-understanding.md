# From Media to Movie Understanding

Persian companion: [2026-07-20-media-to-movie-understanding-fa.md](2026-07-20-media-to-movie-understanding-fa.md)

**Status:** 🧪 research finding — no implementation change

## Question / decision

What do the media types and movie-understanding stages used by SceneForge mean, in execution order, and which current choices are appropriate for a local AMD RX 6900 XT / Windows-DirectML-oriented path?

## Scope and sub-questions

1. What is the role of source video, extracted images/frames, and audio?
2. What does the current stack actually infer at each stage?
3. Where is the distinction between a visual cut/shot and a narrative scene important?
4. Which parts are practical on the target hardware today?

## TL;DR

✅ SceneForge already follows a strong, reusable order: preserve source media; probe it; derive time-stamped frames, audio/transcript segments, and visual cut boundaries; then turn their overlap into queryable scene records. This mirrors the multimodal evidence used in movie-understanding research rather than treating one caption as the whole movie.[^7]

⚠️ The current `PySceneDetectProvider` detects **shot/cut boundaries**, not necessarily narrative scenes. It is a sound deterministic first segmentation, but the project should call its output `shot` or `visual segment` unless and until a temporal scene-segmentation model merges shots into narrative scenes.[^3][^7]

✅ FFmpeg/ffprobe, PySceneDetect, and the current OpenCV Haar cascade are CPU-local and need neither CUDA nor DirectML. `faster-whisper` can remain a configurable local option; a future ONNX face/vision provider can use Windows DirectML on the RX 6900 XT, but DirectML is now in sustained engineering and new Windows ONNX Runtime development is moving to WinML.[^1][^8]

## Findings: media and movie, in order

### 1. Source movie / video — the canonical evidence

✅ A `VideoMedia` is the immutable identity and source reference for the film or clip. It is **not** the decoded pixels or a model-specific result. Keeping that source identity lets all later artifacts remain traceable to one movie and permits caching/reuse.

✅ First enrich it with container and stream facts: duration, codec, frame rate, dimensions, audio tracks, subtitles, chapters, and time bases. `ffprobe` is designed to report container and stream information in human- and machine-readable forms, so it is an appropriate authoritative probe before timestamp-based work.[^1]

**Why it matters:** every downstream time range must use the same clock. A wrong duration or frame rate causes mis-assigned frames, transcripts, and scene boundaries.

### 2. Video frames — sampled visual evidence

✅ A frame is one image at a known video timestamp. SceneForge uses FFmpeg to derive evenly spaced PNG frames and stores their paths plus timestamps as `FrameExtractionArtifact`s. FFmpeg is the right local decoding/extraction layer; it also exposes frame-rate processing through documented filters.[^2]

⚠️ Even sampling is excellent for previews, coarse retrieval, and inexpensive scene summaries, but it can miss short actions, edits, or faces between samples. For high-recall tasks, sample around detected boundaries and/or use a denser adaptive policy.

**What an image/frame can support now:** dimensions and file facts, face boxes, OCR, image embeddings, captions, object detection, shot composition, and later visual-language-model descriptions. A frame alone does not establish identity persistence, action duration, or story causality.

### 3. Audio — the spoken and acoustic timeline

✅ Audio is a separate `AudioMedia` view of the same source or can be read from the video directly. It supplies dialogue, language, music, silence, and sound-event evidence that pixels cannot provide.

✅ SceneForge’s injected `faster-whisper` provider emits time-bounded transcript segments. The upstream Whisper family is a multilingual sequence-to-sequence speech-recognition/translation model; its official model card explicitly warns that results vary by language and can contain speech that was not present.[^4][^5]

⚠️ Therefore transcripts should remain evidence with timestamps and confidence/quality metadata where available, never unquestioned ground truth. Dialogue spanning a boundary should overlap both adjoining visual segments, as SceneForge already does.

### 4. Visual boundaries — cuts/shots before narrative scenes

✅ PySceneDetect `ContentDetector` detects rapid cuts from changes in adjacent-frame colour and intensity. Its adaptive detector can reduce false positives caused by fast camera motion using a rolling comparison.[^3]

⚠️ In film language, a **shot** is uninterrupted camera coverage; a **narrative scene** is a coherent dramatic unit and can contain many shots. The current provider’s own description says “scene (shot) boundaries”; the artifact should be interpreted as a visual segmentation baseline, not semantic scene understanding.

✅ MovieNet supports this distinction: it includes scene-boundary annotations alongside character, action/place, aligned-description, and cinematic-style information, and defines scene segmentation as a distinct boundary-detection task.[^7]

**Practical implication:** retain the current fast cut detector, but make `shot` explicit in schema/documentation. Add an optional later stage that groups shots using visual, dialogue, location, and temporal context.

### 5. Face detection on frames — presence, not identity

✅ SceneForge uses OpenCV’s bundled Haar cascade on each extracted image. `detectMultiScale` returns face bounding rectangles, so this stage can answer “how many detectable frontal faces are in this frame, and where?”[^6]

⚠️ It cannot reliably answer “who is this character?” or track one person across edits. Haar cascades are a lightweight baseline and need validation against real target footage, especially for profile faces, occlusion, low light, makeup, motion blur, and diverse casts.

**Next semantic step:** use detector boxes as observations; add face embeddings plus temporal association only after defining consent, retention, and evaluation rules. Character identity is a separate, higher-risk capability.

### 6. Knowledge builders — align evidence by time and provenance

✅ `SceneGroupingBuilder` assigns frames to half-open visual ranges and assigns transcript segments to every range they overlap. `SceneFaceBuilder` joins frame-face observations through the extracted frame path. This produces reproducible scene/shot records with explicit parent artifacts instead of hidden model state.

✅ This is the right bridge from raw media to a movie knowledge graph: MovieNet’s multimodal annotations similarly combine boundaries with character, place/action, descriptions, and cinematic-style evidence.[^7]

⚠️ A numeric face total is evidence about sampled frames, not a count of unique characters or people in the full segment. Preserve sample density and detector settings in metadata so later comparisons remain meaningful.

### 7. Movie-level understanding, search, and reasoning — derived, never regenerated

📋 Once each visual segment has time-aligned frames, transcript, and optional detections/embeddings, a movie record can support retrieval (“find dialogue about X”), analytics (“segments with many faces”), and later narrative reasoning. SceneForge’s artifact persistence and immutable provenance are well suited to this reuse.

⚠️ Do not claim character arcs, motivation, theme, or plot causality from the current artifacts alone. Those require additional tested providers and an evidence-aware reasoning layer; the project correctly lists them as intelligence-layer goals rather than current facts.

## Comparison

| Ordered stage | Current SceneForge mechanism | Output / meaning | Fits AMD / DirectML? | Maturity |
|---|---|---|---|---|
| Source video | `VideoMedia`, local loader | Immutable identity and source path | ✅ Yes; no GPU required | ✅ |
| Probe | `FFprobeEnricher` | Duration, codec, fps and stream facts | ✅ CPU-local | ✅ |
| Frame extraction | FFmpeg provider | Timestamped PNG visual samples | ✅ CPU-local | ✅ |
| Audio/transcription | injected `faster-whisper` | Timestamped spoken-text segments | 🧪 CPU works; GPU backend must be selected/tested | 🧪 |
| Cut/shot detection | PySceneDetect `ContentDetector` | Visual cut boundaries, not semantic scenes | ✅ CPU-local | ✅ |
| Face detection | OpenCV Haar cascade | Per-frame face bounding boxes/counts | ✅ CPU-local | 🧪 |
| Knowledge assembly | Scene grouping, face, merge, sequence builders | Provenance-linked visual-segment records | ✅ No GPU required | ✅ |
| Semantic scene grouping / character ID | Not implemented | Narrative scenes; persistent character identities | 🧪 Candidate ONNX provider; validate on target hardware | 📋 |

## Hardware-reality filter

✅ The project’s implemented foundation is portable: FFmpeg, ffprobe, PySceneDetect, and OpenCV run locally without CUDA. The RX 6900 XT is therefore not a dependency for the first complete pipeline.

🧪 For new ONNX-based vision providers on Windows, ONNX Runtime’s DirectML execution provider supports DirectX 12-capable AMD hardware; however, its official documentation says DirectML is in sustained engineering and directs new Windows deployment work toward WinML.[^8] Treat DirectML as an evaluated backend, not a blanket compatibility guarantee: export a small model to a supported ONNX opset, run a correctness fixture, then benchmark VRAM, latency, and fallback operations on the actual Windows machine.

⚠️ The repository currently uses `faster-whisper`, whereas the cited upstream Whisper documentation describes OpenAI’s reference implementation. Do not transfer the reference implementation’s VRAM/speed table directly to `faster-whisper`; benchmark the chosen model, compute type, backend, language mix, and VAD settings locally.

## Recommendation

1. Keep the existing order and immutable artifact/provenance model.
2. Rename/document current `SceneCutArtifact` output as a **shot / visual segment** where accuracy matters; retain a compatibility alias if the public API already calls it a scene.
3. Add a provider-evaluation fixture set: hard cuts, fades, rapid montage, camera pans, multilingual dialogue/music, and varied real faces. Measure boundary precision/recall, transcript WER/CER, and face-detection precision/recall before changing defaults.
4. Prototype one optional ONNX vision provider on the Windows RX 6900 XT through the currently supported Windows ONNX Runtime route; retain CPU fallback and record provider/backend/model versions in artifacts.
5. Only then design a semantic scene-grouping and character-association specification.

## Status

📋 Findings ready for a follow-up specification. No production code was changed by this research.

## Sources

Accessed 2026-07-20.

[^1]: FFmpeg Project, [ffprobe Documentation](https://ffmpeg.org/ffprobe.html).
[^2]: FFmpeg Project, [FFmpeg Filters Documentation](https://ffmpeg.org/ffmpeg-filters.html).
[^3]: PySceneDetect, [Detection Algorithms](https://www.scenedetect.com/docs/api/detectors.html).
[^4]: OpenAI, [Whisper README](https://github.com/openai/whisper/blob/main/README.md).
[^5]: OpenAI, [Whisper model card](https://github.com/openai/whisper/blob/main/model-card.md).
[^6]: OpenCV, [Cascade Classifier tutorial](https://docs.opencv.org/4.x/db/d28/tutorial_cascade_classifier.html).
[^7]: Huang et al., [MovieNet: A Holistic Dataset for Movie Understanding](https://arxiv.org/abs/2007.10937), 2020.
[^8]: ONNX Runtime, [DirectML Execution Provider](https://onnxruntime.ai/docs/execution-providers/DirectML-ExecutionProvider.html).
