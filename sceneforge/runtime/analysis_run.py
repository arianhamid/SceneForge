"""
SceneForge Analysis Run Manifest (ADR-0024 Phase 0 item 5)

`Pipeline`/`AsyncPipeline` already compute everything a coverage report
needs for a single call -- `PipelineResult.from_cache`, `.attempts`,
and `.duration_seconds`, plus the ad-hoc `context.metadata` keys
(`f"{provider.name}.cache_hit"` etc.) written alongside them. What was
missing was a structured place to accumulate that across a whole
analysis session -- many Media items, many providers -- so a report
can later compute real coverage ("attempted audio transcription on 40
of 42 scenes; 2 skipped, no audio track; 1 failed after 3 attempts")
instead of inferring it from whichever outputs happen to exist.

Unlike `ProcessingContext` (per-single-call state: cancellation, a
loose metadata bag), an `AnalysisRun` is meant to be threaded through
many `Pipeline.run_detailed()`/`AsyncPipeline.run_detailed()` calls and
read back afterward.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class StageOutcome(StrEnum):
    """What happened when a provider was asked to process one Media item."""

    ATTEMPTED = "attempted"
    """The provider ran and returned artifacts (see `StageRecord.cache_hit`
    for whether that was a fresh call or a cache lookup -- both count as
    attempted; a cache hit is not a skip, the question was still answered)."""

    SKIPPED = "skipped"
    """The provider never ran -- e.g. `IncompatibleMediaError`, because this
    Media doesn't have the modality this provider needs."""

    FAILED = "failed"
    """The provider ran and raised; retries (if any) were exhausted."""


@dataclass(frozen=True, slots=True)
class StageRecord:
    """One provider's outcome for one Media item, within an `AnalysisRun`."""

    provider_name: str
    provider_version: str
    media_id: UUID
    outcome: StageOutcome
    cache_hit: bool = False
    duration_seconds: float = 0.0
    attempts: int = 0
    error: str | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class AnalysisRun:
    """
    Mutable, run-scoped manifest recording every stage outcome across a
    whole analysis session.

    There is no persistence for `AnalysisRun` itself here -- like
    `EvidenceAnchor`/`EvidenceLink` in ADR-0024 item 3, nothing durable
    consumes one yet (no real Application composes multiple
    providers/media into one session today), so adding a store would
    be solving a problem with no real caller. `coverage()` is the one
    query genuinely needed to make "compute real coverage" concrete;
    further aggregation (per-provider breakdowns, by-media summaries)
    is deferred until a real report needs it.
    """

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    records: list[StageRecord] = field(default_factory=list)

    def record(self, record: StageRecord) -> None:
        self.records.append(record)

    def coverage(self) -> dict[StageOutcome, int]:
        """Count of records by outcome -- the smallest useful summary."""
        counts: dict[StageOutcome, int] = dict.fromkeys(StageOutcome, 0)
        for stage_record in self.records:
            counts[stage_record.outcome] += 1
        return counts
