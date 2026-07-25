"""
SceneForge Fact Extraction Knowledge Builder

Turns `CaptionArtifact`s and `ObjectDetectionArtifact`s
(`Capability.CAPTION`/`Capability.OBJECT_DETECTION`, real since
`TransformersCaptionProvider` and `TransformersObjectDetectionProvider`
-- see `.ai/NEXT_TASK.md` Phase 1) into `Fact`-kind Entities: evidence
converted into an objective, higher-level statement, per ADR-0021's
Understanding Ladder ("Facts" rung). This is the builder ADR-0021
named as blocked, and ADR-0024's entire Phase 0 detour existed to give
a trustworthy foundation to build on.

`CaptionArtifact` support shipped first, alone, matching
`SceneGroupingBuilder`'s own precedent: one real transformation before
generalizing anything. `ObjectDetectionArtifact` support is the second
real case, added specifically to test whether "one Artifact becomes
one Fact" was a real shape or a coincidence of captioning's structure
-- the same "build the second real case, then extract the shared
shape" discipline behind ADR-0011/0016/0018. What that comparison
found:

  * The *count* ("one Artifact -> one Fact") generalized cleanly --
    `ObjectDetectionArtifact` is already one-per-detection (matching
    `FaceDetectionArtifact`'s established shape), so no batching or
    splitting logic was needed here.
  * The *statement text* did not generalize: a caption's `payload` is
    already the statement; a detection's `payload` is unused (`None`)
    -- the statement has to be synthesized from `label` via a small
    template (`f"{label} detected"`). So this builder dispatches per
    artifact type (`_fact_from_caption`, `_fact_from_detection`)
    rather than a single generic "read `.payload`" code path.
  * `Provenance.confidence` gets its first real, non-`None` value here
    -- `ObjectDetectionArtifact.score` maps directly onto a field that
    existed since `Entity.provenance` shipped but had never been
    populated with real data. Captions have no equivalent confidence
    score from the pipeline shape modeled in
    `sceneforge.contrib.transformers_caption`, so caption-derived Facts
    still leave `confidence` as `None` -- an honest gap, not filled
    with a guessed number.

Still deliberately narrow: no deduplication of overlapping detections,
no synthesis across caption/detection/OCR text describing the same
frame, no confidence thresholding beyond whatever the provider's own
`threshold` already applied. Those remain real problems for a third
real case (or a real consumer) to motivate solving. `source_frame_path`
now flows into each Fact's metadata (both artifact types carry it,
matching `FaceDetectionArtifact`/`OCRTextArtifact`'s established
pattern -- a gap in the two `transformers_*` providers caught while
writing the end-to-end example), but no builder correlates it to a
specific `Scene` yet; see `sceneforge.applications.SceneSummary`'s
module docstring for why that's deferred rather than guessed at.

Does not use the ADR-0024 item-3 evidence contract
(`EvidenceAnchor`/`EvidenceLink`): `Entity.provenance.source_artifact_ids`
already gives exactly the traceability those types exist for -- a Fact
Entity resolves back to its source Artifact via `find_artifact_by_id()`
(`sceneforge/core/storage.py`), and neither a caption nor a single
detection's bounding box needs `EvidenceAnchor`'s temporal-interval
shape (spatial region, yes, in principle -- but no consumer reads it
yet, so it isn't populated speculatively). `EvidenceLink`'s real value
is typed relationships *between* Entities (or Entity-to-external-
claim) -- none exist yet for this builder to produce.
"""

from __future__ import annotations

from typing import Any

from sceneforge.contrib.transformers_caption.caption_artifact import CaptionArtifact
from sceneforge.contrib.transformers_object_detection.object_detection_artifact import (
    ObjectDetectionArtifact,
)
from sceneforge.core.artifact import Artifact
from sceneforge.knowledge.entity import Entity, EntityKind, Provenance


class FactExtractionBuilder:
    """
    Converts each `CaptionArtifact`/`ObjectDetectionArtifact` into one
    `Fact`-kind `Entity`.

    Ignores every other artifact type in the input (`SceneCutArtifact`,
    `TranscriptSegmentArtifact`, ...) rather than raising --
    `KnowledgeBuilder`'s docstring says a builder "may read across
    multiple providers' output for the same media," and a batch handed
    to this builder may legitimately contain artifacts this rung
    doesn't care about yet. Contrast with `SceneGroupingBuilder`, which
    raises when its one *required* input (`SceneCutArtifact`) is
    missing -- neither captions nor detections have an equivalent
    required companion artifact to be missing.
    """

    @property
    def name(self) -> str:
        return "fact_extraction"

    @property
    def version(self) -> str:
        return "1.0.0"

    def build(self, artifacts: list[Artifact[Any]]) -> list[Entity[Any]]:
        entities: list[Entity[Any]] = []
        for artifact in artifacts:
            entity: Entity[Any] | None
            if isinstance(artifact, CaptionArtifact):
                entity = self._fact_from_caption(artifact)
            elif isinstance(artifact, ObjectDetectionArtifact):
                entity = self._fact_from_detection(artifact)
            else:
                continue
            if entity is not None:
                entities.append(entity)
        return entities

    def _fact_from_caption(self, artifact: CaptionArtifact) -> Entity[Any] | None:
        if not artifact.payload:
            return None  # an empty caption isn't a statement worth keeping
        return Entity(
            kind=EntityKind.FACT,
            builder=self.name,
            payload=artifact.payload,
            parents=(artifact.id,),
            provenance=Provenance(
                builder=self.name,
                source_artifact_ids=(artifact.id,),
            ),
            metadata={
                "media_id": str(artifact.media_id),
                "statement_type": "caption",
                "source_provider": artifact.provider,
                "prompt": artifact.prompt,
                "source_frame_path": artifact.source_frame_path,
            },
        )

    def _fact_from_detection(
        self, artifact: ObjectDetectionArtifact
    ) -> Entity[Any] | None:
        if not artifact.label:
            return None  # a detection with no label isn't a statement worth keeping
        return Entity(
            kind=EntityKind.FACT,
            builder=self.name,
            payload=f"{artifact.label} detected",
            parents=(artifact.id,),
            provenance=Provenance(
                builder=self.name,
                source_artifact_ids=(artifact.id,),
                confidence=artifact.score,
            ),
            metadata={
                "media_id": str(artifact.media_id),
                "statement_type": "object_detection",
                "source_provider": artifact.provider,
                "label": artifact.label,
                "bounding_box": {
                    "x_min": artifact.x_min,
                    "y_min": artifact.y_min,
                    "x_max": artifact.x_max,
                    "y_max": artifact.y_max,
                },
                "source_frame_path": artifact.source_frame_path,
            },
        )
