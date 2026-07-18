"""
SceneForge Scene Grouping Knowledge Builder

SceneForge's first real Knowledge Builder: turns the three real
artifact types shipped so far (FrameExtractionArtifact,
SceneCutArtifact, TranscriptSegmentArtifact) into `SceneEntity`
objects -- one per detected scene, carrying the frames and transcript
text that fall within that scene's time range.

This is deliberately the smallest useful Knowledge Builder rather than
an attempt at the full Knowledge Graph: it groups by simple time
overlap, produces one Entity kind, and persists nothing itself. See
`docs/philosophy/VISION.md` principle 7 and `.ai/NEXT_TASK.md`'s
Sprint 3 objective for why the scope stops here -- this exists to
prove the Knowledge layer's shape against real artifacts, not to be
the last word on scene understanding.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import UUID

from sceneforge.contrib.ffmpeg.frame_extraction_artifact import FrameExtractionArtifact
from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact
from sceneforge.contrib.whisper.transcript_artifact import TranscriptSegmentArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.exceptions import KnowledgeBuilderError


class SceneGroupingBuilder:
    """
    Groups frame and transcript artifacts into the SceneCutArtifact
    time ranges they fall within, producing one `SceneEntity` per
    detected scene.

    Requires at least one `SceneCutArtifact` per `media_id` present in
    the input -- there's no reasonable way to group by scene without
    scene boundaries, and guessing them would be exactly the kind of
    silent, unpredictable behavior `docs/ARCHITECTURAL_PRINCIPLES.md`
    ("prefer boring over clever") warns against. Run
    `PySceneDetectProvider` first.

    Frames are assigned to the scene whose half-open time range
    `[start_seconds, end_seconds)` contains the frame's timestamp.
    Transcript segments are assigned to every scene they overlap at
    all -- a segment spanning a cut legitimately belongs to both.
    """

    @property
    def name(self) -> str:
        return "scene_grouping"

    @property
    def version(self) -> str:
        return "1.0.0"

    def build(self, artifacts: list[Artifact[Any]]) -> list[Entity[Any]]:
        by_media: dict[UUID, list[Artifact[Any]]] = defaultdict(list)
        for artifact in artifacts:
            media_id = getattr(artifact, "media_id", None)
            if media_id is None:
                continue  # not groupable by this builder without a media_id
            by_media[media_id].append(artifact)

        entities: list[Entity[Any]] = []
        for media_id, media_artifacts in by_media.items():
            entities.extend(self._build_for_media(media_id, media_artifacts))
        return entities

    def _build_for_media(
        self, media_id: UUID, artifacts: list[Artifact[Any]]
    ) -> list[Entity[Any]]:
        scene_cuts = sorted(
            (a for a in artifacts if isinstance(a, SceneCutArtifact)),
            key=lambda a: a.scene_index,
        )
        if not scene_cuts:
            raise KnowledgeBuilderError(
                f"No SceneCutArtifact found for media {media_id} -- "
                "SceneGroupingBuilder needs scene boundaries to group by. "
                "Run PySceneDetectProvider first."
            )

        frames = [a for a in artifacts if isinstance(a, FrameExtractionArtifact)]
        segments = [a for a in artifacts if isinstance(a, TranscriptSegmentArtifact)]

        entities: list[Entity[Any]] = []
        for cut in scene_cuts:
            scene_frames = [
                f
                for f in frames
                if cut.start_seconds <= f.timestamp_seconds < cut.end_seconds
            ]
            scene_frames.sort(key=lambda f: f.timestamp_seconds)

            scene_segments = [
                s
                for s in segments
                if self._overlaps(
                    s.start_seconds, s.end_seconds, cut.start_seconds, cut.end_seconds
                )
            ]
            scene_segments.sort(key=lambda s: s.start_seconds)

            transcript_text = " ".join(
                s.payload for s in scene_segments if s.payload
            ).strip()

            parent_artifacts: list[Artifact[Any]] = [
                cut,
                *scene_frames,
                *scene_segments,
            ]
            parents = tuple(a.id for a in parent_artifacts)

            entities.append(
                Entity(
                    kind=EntityKind.SCENE,
                    builder=self.name,
                    payload=transcript_text or None,
                    parents=parents,
                    metadata={
                        "media_id": str(media_id),
                        "scene_index": cut.scene_index,
                        "start_seconds": cut.start_seconds,
                        "end_seconds": cut.end_seconds,
                        "frame_paths": [f.frame_path for f in scene_frames],
                        "transcript_segment_count": len(scene_segments),
                    },
                )
            )
        return entities

    @staticmethod
    def _overlaps(a_start: float, a_end: float, b_start: float, b_end: float) -> bool:
        return a_start < b_end and b_start < a_end
