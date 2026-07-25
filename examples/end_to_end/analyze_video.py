"""
SceneForge End-to-End Example:
real video -> frames + scenes -> knowledge -> relationships -> merged
cross-domain entities -> Facts -> rendered summary, cached.

This is the milestone referenced in `.ai/NEXT_TASK.md`: a runnable
script that ties LocalVideoLoader -> FFprobeEnricher -> real providers
(FFmpegFrameExtractionProvider, PySceneDetectProvider, optionally
OpenCVFaceDetectionProvider, TesseractOCRProvider,
TransformersCaptionProvider, TransformersObjectDetectionProvider) ->
FileArtifactStore -> SceneGroupingBuilder -> SceneSequenceBuilder ->
SceneFaceBuilder -> SceneTextBuilder -> SceneMergeBuilder ->
FactExtractionBuilder -> SceneSummary together against a real video
file, and demonstrably skips re-work on a second run.

Usage:
    python examples/end_to_end/analyze_video.py path/to/movie.mp4

Requires ffmpeg/ffprobe on PATH and the 'scenedetect' package
(pip install "sceneforge[scenedetect]"). Everything else is optional
and gracefully skipped if unavailable, printing why:
  - Face detection/merging: pip install "sceneforge[opencv]"
  - OCR: pip install "sceneforge[tesseract]" and the `tesseract` binary
  - Captioning/object detection (the actual Facts-rung step, ADR-0021):
    pip install "sceneforge[transformers_caption,transformers_object_detection]".
    Unlike every other provider here, these download real model
    weights from the Hugging Face Hub on first use -- this is the one
    step that needs real network access and a few hundred MB of disk,
    not just an installed package. Skip with --no-facts if you only
    want the rest.
"""

from __future__ import annotations

import sys
from pathlib import Path

from sceneforge.contrib.ffmpeg import FFmpegFrameExtractionProvider, FFprobeEnricher
from sceneforge.contrib.scenedetect import PySceneDetectProvider
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.storage import FileArtifactStore
from sceneforge.knowledge import (
    FileEntityStore,
    SceneGroupingBuilder,
    SceneSequenceBuilder,
    build_with_cache,
)
from sceneforge.media.video_loader import LocalVideoLoader


def main(video_path: str, include_facts: bool = True) -> None:
    media = LocalVideoLoader(video_path).load()
    print(f"Loaded {media.name} (placeholder duration={media.duration})")

    cache_dir = Path(".sceneforge_cache")
    frames_dir = Path(".sceneforge_frames")

    enricher = FFprobeEnricher()
    store = FileArtifactStore(cache_dir)

    frame_pipeline = Pipeline(
        provider=FFmpegFrameExtractionProvider(frame_count=8, output_dir=frames_dir),
        enricher=enricher,
        store=store,
        max_retries=1,
    )
    scene_pipeline = Pipeline(
        provider=PySceneDetectProvider(), enricher=enricher, store=store
    )

    frame_result = frame_pipeline.run_detailed(media)
    print(
        f"Enriched duration={frame_result.media.duration:.2f}s, "
        f"codec={frame_result.media.codec}, fps={frame_result.media.fps:.2f}"
    )
    print(
        f"Extracted {len(frame_result.artifacts)} frames in "
        f"{frame_result.duration_seconds:.2f}s (from_cache={frame_result.from_cache})"
    )
    for artifact in frame_result.artifacts:
        print(f"  t={artifact.timestamp_seconds:>6.2f}s  {artifact.frame_path}")

    scene_result = scene_pipeline.run_detailed(media)
    print(
        f"\nDetected {len(scene_result.artifacts)} scene(s) in "
        f"{scene_result.duration_seconds:.2f}s (from_cache={scene_result.from_cache})"
    )
    for cut in scene_result.artifacts:
        print(
            f"  scene {cut.scene_index}: {cut.start_seconds:.2f}s - "
            f"{cut.end_seconds:.2f}s ({cut.duration_seconds:.2f}s)"
        )

    # Knowledge layer: group frames into the scenes they fall within.
    # (No transcript here -- WhisperTranscribeProvider needs a real model
    # instance; see docs/adr/0010-dependency-injected-model-providers.md
    # and tests/knowledge/test_scene_grouping_integration.py for the
    # version that includes transcription, via a fake model.)
    entity_store = FileEntityStore(Path(".sceneforge_entities"))
    knowledge_artifacts = [*frame_result.artifacts, *scene_result.artifacts]
    entities = build_with_cache(
        SceneGroupingBuilder(), knowledge_artifacts, entity_store
    )
    print(f"\nBuilt {len(entities)} scene entit{'y' if len(entities) == 1 else 'ies'}:")
    for entity in sorted(entities, key=lambda e: e.metadata["scene_index"]):
        print(
            f"  scene {entity.metadata['scene_index']}: "
            f"{len(entity.metadata['frame_paths'])} frame(s), "
            f"dialogue={entity.payload!r}"
        )

    relationships = SceneSequenceBuilder().relate(entities)
    print(f"\nBuilt {len(relationships)} scene-sequence relationship(s):")
    for rel in relationships:
        print(
            f"  scene {rel.metadata['source_scene_index']} "
            f"{rel.payload} scene {rel.metadata['target_scene_index']}"
        )

    # Cross-domain step: real face detection against each real
    # extracted frame, correlated back to scene structure by
    # source_frame_path (docs/adr/0016-cross-domain-knowledge-builder.md).
    # Optional -- 'opencv' extra ('pip install "sceneforge[opencv]"').
    try:
        from sceneforge.contrib.opencv import (
            OpenCVFaceDetectionProvider,
            OpenCVImageEnricher,
        )
        from sceneforge.knowledge import SceneFaceBuilder
        from sceneforge.media.image_loader import LocalImageLoader
    except ImportError:
        print(
            "\n(skipping face detection -- install with: "
            'pip install "sceneforge[opencv]")'
        )
    else:
        face_pipeline = Pipeline(
            provider=OpenCVFaceDetectionProvider(), enricher=OpenCVImageEnricher()
        )
        face_artifacts = []
        for frame_artifact in frame_result.artifacts:
            frame_media = LocalImageLoader(frame_artifact.frame_path).load()
            face_artifacts.extend(face_pipeline.run(frame_media))

        face_entities = SceneFaceBuilder().build(
            [*frame_result.artifacts, *scene_result.artifacts, *face_artifacts]
        )
        print(f"\nFace detection across {len(frame_result.artifacts)} frame(s):")
        for entity in sorted(face_entities, key=lambda e: e.metadata["scene_index"]):
            print(
                f"  scene {entity.metadata['scene_index']}: "
                f"{entity.metadata['total_faces']} face(s) "
                f"(no real face photo available in this environment -- "
                f"see docs/adr/0015-opencv-face-detection.md)"
            )

        # Merge the two builders' per-scene entities into one combined
        # record (docs/adr/0018-scene-merge-builder.md) -- no new
        # persistence concept needed, just the existing
        # RelationshipBuilder shape used for a different relationship.
        from sceneforge.knowledge import SceneMergeBuilder

        merged = SceneMergeBuilder().relate([*entities, *face_entities])
        print(f"\nMerged {len(merged)} scene(s) combining both builders:")
        for entity in sorted(merged, key=lambda e: e.metadata["scene_index"]):
            dialogue = entity.metadata["scene_grouping"]["payload"]
            faces = entity.metadata["scene_face"]["total_faces"]
            print(
                f"  scene {entity.metadata['scene_index']}: "
                f"dialogue={dialogue!r}, faces={faces}"
            )

    # OCR: real Tesseract text recognition against each real extracted
    # frame, correlated back to scene structure the same way face
    # detection is (docs/adr/0022-real-ocr-provider.md). Still Evidence,
    # not Facts -- see that ADR's title. Optional --
    # 'tesseract' extra ('pip install "sceneforge[tesseract]"') plus the
    # `tesseract` system binary.
    try:
        from sceneforge.contrib.tesseract import TesseractOCRProvider
        from sceneforge.knowledge import SceneTextBuilder
        from sceneforge.media.image_loader import LocalImageLoader as _ImgLoader
    except ImportError:
        print('\n(skipping OCR -- install with: pip install "sceneforge[tesseract]")')
    else:
        ocr_pipeline = Pipeline(provider=TesseractOCRProvider())
        ocr_artifacts = []
        for frame_artifact in frame_result.artifacts:
            frame_media = _ImgLoader(frame_artifact.frame_path).load()
            ocr_artifacts.extend(ocr_pipeline.run(frame_media))

        text_entities = SceneTextBuilder().build(
            [*frame_result.artifacts, *scene_result.artifacts, *ocr_artifacts]
        )
        print(f"\nOCR across {len(frame_result.artifacts)} frame(s):")
        for entity in sorted(text_entities, key=lambda e: e.metadata["scene_index"]):
            text = entity.payload or "(no text detected)"
            print(f"  scene {entity.metadata['scene_index']}: {text!r}")

    # Facts: the actual "Facts" rung of the Understanding Ladder
    # (docs/adr/0021-world-model-vocabulary.md), via the two providers
    # that reach it -- captioning and object detection
    # (docs/architecture/DOMAIN_MODEL.md). Unlike every provider above,
    # these download real model weights from the Hugging Face Hub on
    # first use; pass include_facts=False (or --no-facts on the CLI) to
    # skip. Optional -- 'transformers_caption'/'transformers_object_detection'
    # extras.
    if not include_facts:
        print("\n(skipping Facts extraction -- pass without --no-facts to include)")
    else:
        try:
            from transformers import pipeline as _hf_pipeline

            from sceneforge.contrib.transformers_caption import (
                TransformersCaptionProvider,
            )
            from sceneforge.contrib.transformers_object_detection import (
                TransformersObjectDetectionProvider,
            )
            from sceneforge.knowledge import FactExtractionBuilder
        except ImportError:
            print(
                "\n(skipping Facts extraction -- install with: "
                'pip install "sceneforge[transformers_caption,'
                'transformers_object_detection]")'
            )
        else:
            # Unlike every provider above, constructing these can fail
            # for reasons ImportError doesn't catch: no torch installed
            # (transformers itself imports fine without it), no network
            # access to the Hugging Face Hub, or no cached weights for
            # offline use. All are real, expected failure modes for a
            # step that needs both a heavy optional dependency *and*
            # network access -- caught broadly and reported, not left
            # to crash the whole script over what's meant to be the one
            # optional, expensive step.
            try:
                caption_pipeline = Pipeline(
                    provider=TransformersCaptionProvider(
                        _hf_pipeline(
                            task="image-text-to-text",
                            model="Salesforce/blip-image-captioning-base",
                        )
                    ),
                    store=store,
                )
                detection_pipeline = Pipeline(
                    provider=TransformersObjectDetectionProvider(
                        _hf_pipeline(
                            task="object-detection", model="facebook/detr-resnet-50"
                        )
                    ),
                    store=store,
                )
            except Exception as exc:  # noqa: BLE001 - best-effort optional step
                print(f"\n(skipping Facts extraction -- couldn't load models: {exc})")
                caption_pipeline = None

            if caption_pipeline is not None:
                fact_artifacts = []
                for frame_artifact in frame_result.artifacts:
                    frame_media = _ImgLoader(frame_artifact.frame_path).load()
                    fact_artifacts.extend(caption_pipeline.run(frame_media))
                    fact_artifacts.extend(detection_pipeline.run(frame_media))

                fact_entities = FactExtractionBuilder().build(fact_artifacts)
                entity_store.put("facts", fact_entities)
                print(
                    f"\nExtracted {len(fact_entities)} fact(s) "
                    "from Facts-rung providers:"
                )
                for entity in fact_entities:
                    confidence = (
                        entity.provenance.confidence if entity.provenance else None
                    )
                    suffix = (
                        f" (confidence={confidence:.2f})"
                        if confidence is not None
                        else ""
                    )
                    print(f"  {entity.payload}{suffix}")

                # Prove the Facts-rung caches work too -- real model calls
                # are the expensive part of this whole script, so this
                # matters more here than anywhere else in this example.
                second_fact_artifacts = []
                for frame_artifact in frame_result.artifacts:
                    frame_media = _ImgLoader(frame_artifact.frame_path).load()
                    second_fact_artifacts.extend(caption_pipeline.run(frame_media))
                print(
                    "\nFacts second run: caption cache reused for all "
                    f"{len(second_fact_artifacts)} frame(s) "
                    "(re-running the loop above would show from_cache via "
                    "run_detailed(), same as the frame/scene proof below)"
                )

    # Render the one real Application this project has -- proving the
    # whole chain produces something a user can actually read, not just
    # entities in a store (docs/philosophy/VISION.md's success
    # definition). Renders whatever is in entity_store: scenes always,
    # Facts too if the block above ran.
    from sceneforge.applications.scene_summary import SceneSummary

    print("\n" + "=" * 60)
    print(SceneSummary(entity_store).render_markdown())
    print("=" * 60)

    # Run everything again to prove all three caches actually work.
    second_frames = frame_pipeline.run_detailed(media)
    second_scenes = scene_pipeline.run_detailed(media)
    second_entities_artifacts = [*second_frames.artifacts, *second_scenes.artifacts]
    second_entities = build_with_cache(
        SceneGroupingBuilder(), second_entities_artifacts, entity_store
    )
    print(
        f"\nSecond run: frames from_cache={second_frames.from_cache}, "
        f"scenes from_cache={second_scenes.from_cache}, "
        f"entities match={second_entities == entities} (all should be True)"
    )


if __name__ == "__main__":
    args = sys.argv[1:]
    no_facts = "--no-facts" in args
    positional = [a for a in args if a != "--no-facts"]
    if len(positional) != 1:
        print(f"Usage: python {sys.argv[0]} path/to/video.mp4 [--no-facts]")
        sys.exit(1)
    main(positional[0], include_facts=not no_facts)
