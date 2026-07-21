"""
SceneForge Scene Text Knowledge Builder

Groups recognized on-screen text into the scenes their source frames
fall within -- the same cross-domain correlation pattern as
`SceneFaceBuilder` (ADR-0016), swapping `FaceDetectionArtifact` for
`OCRTextArtifact`. Both artifact types carry `source_frame_path`
(auto-populated by their respective providers from the decoded
image's own metadata), so correlating either one back to
`FrameExtractionArtifact.frame_path` needs no `media_id` relinking --
confirming ADR-0016's finding held for a second real capability, not
just the one it was built for.

Honest scope note (see docs/adr/0021-world-model-vocabulary.md and
docs/adr/0022-real-ocr-provider.md): grouping recognized text by scene
is still the Evidence layer, organized -- the same rung
`SceneGroupingBuilder` and `SceneFaceBuilder` already occupy. A sign
reading "POLICE STATION" becoming the Fact "this location is a police
station" needs a semantic interpretation step this builder does not
attempt. This builder makes text queryable per scene; it does not
claim to understand what the text means.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import UUID

from sceneforge.contrib.ffmpeg.frame_extraction_artifact import FrameExtractionArtifact
from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact
from sceneforge.contrib.tesseract.ocr_artifact import OCRTextArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.exceptions import KnowledgeBuilderError


class SceneTextBuilder:
    """
    Groups OCR text detections into the scenes their source frames
    fall within, producing one Entity per scene with the recognized
    text (in reading order: top-to-bottom, then left-to-right within a
    frame; frames in timestamp order) and a per-frame breakdown.

    Requires at least one `SceneCutArtifact` per `media_id`, the same
    precondition every scene-grouping builder in this codebase shares.
    `OCRTextArtifact`s are matched to frames by
    `source_frame_path == FrameExtractionArtifact.frame_path` -- their
    own `media_id` (belonging to the per-frame `ImageMedia`, not the
    video) is not used for grouping, the same as `SceneFaceBuilder`.
    """

    @property
    def name(self) -> str:
        return "scene_text"

    @property
    def version(self) -> str:
        return "1.0.0"

    def build(self, artifacts: list[Artifact[Any]]) -> list[Entity[Any]]:
        by_media: dict[UUID, list[Artifact[Any]]] = defaultdict(list)
        text_by_frame_path: dict[str, list[OCRTextArtifact]] = defaultdict(list)

        for artifact in artifacts:
            if isinstance(artifact, OCRTextArtifact):
                if artifact.source_frame_path:
                    text_by_frame_path[artifact.source_frame_path].append(artifact)
                continue
            media_id = getattr(artifact, "media_id", None)
            if media_id is None:
                continue
            by_media[media_id].append(artifact)

        entities: list[Entity[Any]] = []
        for media_id, media_artifacts in by_media.items():
            entities.extend(
                self._build_for_media(media_id, media_artifacts, text_by_frame_path)
            )
        return entities

    def _build_for_media(
        self,
        media_id: UUID,
        artifacts: list[Artifact[Any]],
        text_by_frame_path: dict[str, list[OCRTextArtifact]],
    ) -> list[Entity[Any]]:
        scene_cuts = sorted(
            (a for a in artifacts if isinstance(a, SceneCutArtifact)),
            key=lambda a: a.scene_index,
        )
        if not scene_cuts:
            raise KnowledgeBuilderError(
                f"No SceneCutArtifact found for media {media_id} -- "
                "SceneTextBuilder needs scene boundaries to group by. "
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

            text_per_frame: dict[str, str] = {}
            all_words: list[str] = []
            parent_ids = [cut.id, *(f.id for f in scene_frames)]
            for frame in scene_frames:
                words = sorted(
                    text_by_frame_path.get(frame.frame_path, []),
                    key=lambda w: w.word_index,
                )
                frame_text = " ".join(w.payload for w in words if w.payload)
                text_per_frame[frame.frame_path] = frame_text
                if frame_text:
                    all_words.append(frame_text)
                parent_ids.extend(w.id for w in words)

            entities.append(
                Entity(
                    kind=EntityKind.SCENE,
                    builder=self.name,
                    payload=" / ".join(all_words) or None,
                    parents=tuple(parent_ids),
                    metadata={
                        "media_id": str(media_id),
                        "scene_index": cut.scene_index,
                        "start_seconds": cut.start_seconds,
                        "end_seconds": cut.end_seconds,
                        "text_per_frame": text_per_frame,
                    },
                )
            )
        return entities
