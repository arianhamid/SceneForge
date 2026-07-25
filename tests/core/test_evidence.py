"""Tests for the evidence contract (ADR-0024 Phase 0 item 3)."""

from uuid import uuid4

import pytest

from sceneforge.core.evidence import (
    EvidenceAnchor,
    EvidenceLink,
    EvidenceRelation,
    Reference,
    ReferenceKind,
)


def test_evidence_anchor_holds_a_presentation_interval():
    media_id = uuid4()
    anchor = EvidenceAnchor(media_id=media_id, start_seconds=1.0, end_seconds=3.5)

    assert anchor.media_id == media_id
    assert anchor.start_seconds == 1.0
    assert anchor.end_seconds == 3.5


def test_evidence_anchor_rejects_end_before_start():
    with pytest.raises(ValueError, match="must not precede"):
        EvidenceAnchor(media_id=uuid4(), start_seconds=5.0, end_seconds=1.0)


def test_evidence_anchor_allows_equal_start_and_end_as_a_point():
    anchor = EvidenceAnchor(media_id=uuid4(), start_seconds=2.0, end_seconds=2.0)
    assert anchor.start_seconds == anchor.end_seconds


def test_evidence_anchor_rejects_malformed_spatial_region():
    with pytest.raises(ValueError, match="spatial_region"):
        EvidenceAnchor(media_id=uuid4(), spatial_region=(0.1, 0.2, 0.3))  # type: ignore[arg-type]


def test_evidence_anchor_accepts_a_valid_spatial_region():
    anchor = EvidenceAnchor(media_id=uuid4(), spatial_region=(0.1, 0.2, 0.3, 0.4))
    assert anchor.spatial_region == (0.1, 0.2, 0.3, 0.4)


def test_evidence_anchor_edition_id_defaults_to_none():
    """Reserved field, unpopulated until Media has real edition identity
    (ADR-0024 item 2 deferred that field)."""
    anchor = EvidenceAnchor(media_id=uuid4())
    assert anchor.edition_id is None


def test_evidence_anchor_is_immutable():
    anchor = EvidenceAnchor(media_id=uuid4())
    with pytest.raises(AttributeError):
        anchor.start_seconds = 9.0  # type: ignore[misc]


def test_reference_distinguishes_kinds_for_the_same_id():
    shared_id = uuid4()
    artifact_ref = Reference(kind=ReferenceKind.ARTIFACT, id=shared_id)
    entity_ref = Reference(kind=ReferenceKind.ENTITY, id=shared_id)

    assert artifact_ref.id == entity_ref.id
    assert artifact_ref != entity_ref
    assert artifact_ref.kind != entity_ref.kind


def test_evidence_link_connects_two_typed_references():
    artifact_ref = Reference(kind=ReferenceKind.ARTIFACT, id=uuid4())
    entity_ref = Reference(kind=ReferenceKind.ENTITY, id=uuid4())

    link = EvidenceLink(
        source=artifact_ref, target=entity_ref, relation=EvidenceRelation.SUPPORTS
    )

    assert link.source == artifact_ref
    assert link.target == entity_ref
    assert link.relation == EvidenceRelation.SUPPORTS


def test_evidence_link_ids_are_unique_per_instance():
    artifact_ref = Reference(kind=ReferenceKind.ARTIFACT, id=uuid4())
    entity_ref = Reference(kind=ReferenceKind.ENTITY, id=uuid4())

    link1 = EvidenceLink(
        source=artifact_ref, target=entity_ref, relation=EvidenceRelation.DERIVED_FROM
    )
    link2 = EvidenceLink(
        source=artifact_ref, target=entity_ref, relation=EvidenceRelation.DERIVED_FROM
    )

    assert link1.id != link2.id


def test_evidence_link_is_immutable():
    link = EvidenceLink(
        source=Reference(kind=ReferenceKind.ARTIFACT, id=uuid4()),
        target=Reference(kind=ReferenceKind.ENTITY, id=uuid4()),
        relation=EvidenceRelation.SUPPORTS,
    )
    with pytest.raises(AttributeError):
        link.relation = EvidenceRelation.DERIVED_FROM  # type: ignore[misc]
