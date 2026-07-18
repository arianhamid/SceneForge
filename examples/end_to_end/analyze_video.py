"""
SceneForge End-to-End Example:
real video -> frames + scenes -> knowledge -> relationships -> merged
cross-domain entities, cached.

This is the milestone referenced in `.ai/NEXT_TASK.md`: a runnable
script that ties LocalVideoLoader -> FFprobeEnricher -> real providers
(FFmpegFrameExtractionProvider, PySceneDetectProvider, optionally
OpenCVFaceDetectionProvider) -> FileArtifactStore ->
SceneGroupingBuilder -> SceneSequenceBuilder -> SceneFaceBuilder ->
SceneMergeBuilder together against a real video file, and demonstrably
skips re-work on a second run.

Usage:
    python examples/end_to_end/analyze_video.py path/to/movie.mp4

Requires ffmpeg/ffprobe on PATH and the 'scenedetect' package
(pip install "sceneforge[scenedetect]"). Face detection and merging
are optional (pip install "sceneforge[opencv]") and gracefully skipped
if unavailable.
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


def main(video_path: str) -> None:
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
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} path/to/video.mp4")
        sys.exit(1)
    main(sys.argv[1])
