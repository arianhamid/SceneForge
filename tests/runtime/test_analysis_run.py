"""Tests for the AnalysisRun manifest (ADR-0024 Phase 0 item 5)."""

from uuid import uuid4

import pytest

from sceneforge.runtime.analysis_run import AnalysisRun, StageOutcome, StageRecord


def _record(outcome: StageOutcome, **kwargs) -> StageRecord:
    return StageRecord(
        provider_name="whisper",
        provider_version="1.0.0",
        media_id=uuid4(),
        outcome=outcome,
        **kwargs,
    )


def test_new_analysis_run_has_no_records():
    run = AnalysisRun()
    assert run.records == []


def test_record_appends_to_records():
    run = AnalysisRun()
    record = _record(StageOutcome.ATTEMPTED)

    run.record(record)

    assert run.records == [record]


def test_record_preserves_order():
    run = AnalysisRun()
    first = _record(StageOutcome.ATTEMPTED)
    second = _record(StageOutcome.SKIPPED)

    run.record(first)
    run.record(second)

    assert run.records == [first, second]


def test_coverage_counts_by_outcome():
    run = AnalysisRun()
    run.record(_record(StageOutcome.ATTEMPTED))
    run.record(_record(StageOutcome.ATTEMPTED))
    run.record(_record(StageOutcome.SKIPPED))
    run.record(_record(StageOutcome.FAILED))

    coverage = run.coverage()

    assert coverage[StageOutcome.ATTEMPTED] == 2
    assert coverage[StageOutcome.SKIPPED] == 1
    assert coverage[StageOutcome.FAILED] == 1


def test_coverage_includes_zero_counts_for_outcomes_never_recorded():
    run = AnalysisRun()
    run.record(_record(StageOutcome.ATTEMPTED))

    coverage = run.coverage()

    assert coverage[StageOutcome.SKIPPED] == 0
    assert coverage[StageOutcome.FAILED] == 0


def test_coverage_on_empty_run_is_all_zero():
    run = AnalysisRun()
    coverage = run.coverage()
    assert all(count == 0 for count in coverage.values())


def test_stage_record_defaults():
    record = StageRecord(
        provider_name="whisper",
        provider_version="1.0.0",
        media_id=uuid4(),
        outcome=StageOutcome.SKIPPED,
    )

    assert record.cache_hit is False
    assert record.duration_seconds == 0.0
    assert record.attempts == 0
    assert record.error is None


def test_stage_record_is_immutable():
    record = _record(StageOutcome.ATTEMPTED)
    with pytest.raises(AttributeError):
        record.outcome = StageOutcome.FAILED  # type: ignore[misc]


def test_analysis_run_ids_are_unique():
    assert AnalysisRun().id != AnalysisRun().id
