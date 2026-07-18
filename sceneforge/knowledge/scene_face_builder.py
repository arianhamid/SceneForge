"""
SceneForge Scene Face Knowledge Builder

The Sprint 9 spike, resolved: SceneForge's first Knowledge Builder
synthesizing across two capability domains at once (video/scene
structure from `ffmpeg`/`scenedetect`, and image/face detection from
`opencv`). Produces one Entity per scene, carrying the total face
count and per-frame breakdown for frames within that scene's time
range -- extending `SceneGroupingBuilder`'s pattern with a second
Artifact type instead of `SceneGroupingBuilder`'s transcript segments.

The real question this resolved (`docs/adr/0016-cross-domain-knowledge-builder.md`):
does correlating `FaceDetectionArtifact`s (produced by running the
face detector against each extracted frame *as its own ImageMedia*,
with its own generated `media_id`) back to the video's scene structure
need a new "Entity + Artifact -> Entity" builder Protocol shape? No --
`FaceDetectionArtifact.source_frame_path` (set by the provider to the
image's own `metadata["source"]`) already equals
`FrameExtractionArtifact.frame_path` when the image is a video frame,
so a plain `KnowledgeBuilder` (`Artifact -> Entity`, matching
`SceneGroupingBuilder`'s existing Protocol) can correlate by path
string equality without ever needing `FaceDetectionArtifact.media_id`
to match the video's `media_id`, and without needing pre-built
`SceneEntity` objects as input.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import UUID

from sceneforge.contrib.ffmpeg.frame_extraction_artifact import FrameExtractionArtifact
from sceneforge.contrib.opencv.face_detection_artifact import FaceDetectionArtifact
from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.exceptions import KnowledgeBuilderError


class SceneFaceBuilder:
    """
    Groups face detections into the scenes their source frames fall
    within, producing one Entity per scene with a face count and a
    per-frame breakdown.

    Requires at least one `SceneCutArtifact` and its `media_id`-matched
    `FrameExtractionArtifact`s, the same precondition
    `SceneGroupingBuilder` has. `FaceDetectionArtifact`s are matched to
    frames by `source_frame_path == FrameExtractionArtifact.frame_path`
    -- their own `media_id` (belonging to the per-frame `ImageMedia`,
    not the video) is not used for grouping at all.
    """

    @property
    def name(self) -> str:
        return "scene_face"

    @property
    def version(self) -> str:
        return "1.0.0"

    def build(self, artifacts: list[Artifact[Any]]) -> list[Entity[Any]]:
        by_media: dict[UUID, list[Artifact[Any]]] = defaultdict(list)
        faces_by_frame_path: dict[str, list[FaceDetectionArtifact]] = defaultdict(list)

        for artifact in artifacts:
            if isinstance(artifact, FaceDetectionArtifact):
                if artifact.source_frame_path:
                    faces_by_frame_path[artifact.source_frame_path].append(artifact)
                continue
            media_id = getattr(artifact, "media_id", None)
            if media_id is None:
                continue
            by_media[media_id].append(artifact)

        entities: list[Entity[Any]] = []
        for media_id, media_artifacts in by_media.items():
            entities.extend(
                self._build_for_media(media_id, media_artifacts, faces_by_frame_path)
            )
        return entities

    def _build_for_media(
        self,
        media_id: UUID,
        artifacts: list[Artifact[Any]],
        faces_by_frame_path: dict[str, list[FaceDetectionArtifact]],
    ) -> list[Entity[Any]]:
        scene_cuts = sorted(
            (a for a in artifacts if isinstance(a, SceneCutArtifact)),
            key=lambda a: a.scene_index,
        )
        if not scene_cuts:
            raise KnowledgeBuilderError(
                f"No SceneCutArtifact found for media {media_id} -- "
                "SceneFaceBuilder needs scene boundaries to group by. "
                "Run PySceneDetectProvider first."
            )

        frames = [a for a in artifacts if isinstance(a, FrameExtractionArtifact)]

        entities: list[Entity[Any]] = []
        for cut in scene_cuts:
            scene_frames = [
                f
                for f in frames
                if cut.start_seconds <= f.timestamp_seconds < cut.end_seconds
            ]
            scene_frames.sort(key=lambda f: f.timestamp_seconds)

            faces_per_frame: dict[str, int] = {}
            total_faces = 0
            parent_ids = [cut.id, *(f.id for f in scene_frames)]
            for frame in scene_frames:
                detections = faces_by_frame_path.get(frame.frame_path, [])
                faces_per_frame[frame.frame_path] = len(detections)
                total_faces += len(detections)
                parent_ids.extend(d.id for d in detections)

            entities.append(
                Entity(
                    kind=EntityKind.SCENE,
                    builder=self.name,
                    payload=total_faces,
                    parents=tuple(parent_ids),
                    metadata={
                        "media_id": str(media_id),
                        "scene_index": cut.scene_index,
                        "start_seconds": cut.start_seconds,
                        "end_seconds": cut.end_seconds,
                        "total_faces": total_faces,
                        "faces_per_frame": faces_per_frame,
                    },
                )
            )
        return entities
