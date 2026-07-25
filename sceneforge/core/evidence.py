"""
SceneForge Evidence Contract (ADR-0024 Phase 0 item 3)

Before this module, nothing let an application resolve a conclusion
back to the evidence that supports it: `Artifact` carried no required
source/interval/anchor fields, `Entity.parents` was an untyped `UUID`
tuple whose meaning depended on which builder produced it, and
`ArtifactStore` had no lookup by artifact ID or media (confirmed by
direct reproduction in the 2026-07-22 implementation review). This
module is the smallest fix for that: a place in the source material a
piece of evidence comes from (`EvidenceAnchor`), and a typed
relationship between two things (`EvidenceLink`).

Deliberately not here: a knowledge graph, a persistence layer for
these types, or a general claim/interpretation model. No builder
produces `EvidenceLink`s yet -- these are types only, the same way
`Entity.provenance` shipped as a type before any builder populated it.
Serialization support (an `EvidenceLink`/`EvidenceAnchor` inside an
`Entity`'s metadata or a dedicated field surviving a JSON round trip)
is deferred until a real builder needs it, rather than added
speculatively now -- adding it ahead of a real consumer is exactly the
pattern ADR-0024 already declined for `Media`'s edition-identity
field, for the same reason.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class ReferenceKind(StrEnum):
    """
    What kind of thing a UUID in an `EvidenceLink` endpoint refers to.

    A bare UUID's meaning already varies by builder in the existing
    `Entity.parents` field -- one builder's parent tuple means "the
    artifacts I was built from," another's means something else
    entirely, and nothing in the type distinguishes them. This
    contract exists specifically not to repeat that ambiguity, so
    every `Reference` names its own kind explicitly.
    """

    ARTIFACT = "artifact"
    ENTITY = "entity"
    EXTERNAL_CLAIM = "external_claim"
    REVISION = "revision"


@dataclass(frozen=True, slots=True)
class Reference:
    """A typed (kind, id) pair -- an `EvidenceLink` endpoint."""

    kind: ReferenceKind
    id: UUID


class EvidenceRelation(StrEnum):
    """
    How a `EvidenceLink`'s source relates to its target.

    Only the two relations ADR-0024 names explicitly. Add more only
    when a real builder needs to express a relationship neither of
    these covers -- this vocabulary has the same "don't grow ahead of
    a real consumer" discipline as everything else in Phase 0.
    """

    SUPPORTS = "supports"
    DERIVED_FROM = "derived_from"


@dataclass(frozen=True, slots=True)
class EvidenceLink:
    """A typed relationship between two things, one of which is evidence for
    the other. `source` and `target` are `Reference`s, not bare UUIDs, so
    the relationship's endpoints are self-describing without consulting
    whichever builder happened to produce them."""

    source: Reference
    target: Reference
    relation: EvidenceRelation
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class EvidenceAnchor:
    """
    Where in the source material a piece of evidence actually comes from.

    The smallest thing that lets an application resolve a conclusion
    back to durable evidence -- not a general provenance record (see
    `Entity.provenance` for "why the system believes it," which is a
    different question from "where does the evidence physically live")
    and not a knowledge-graph node.

    `edition_id` is reserved and typically `None` today: `Media` has
    no edition-identity field yet (ADR-0024 item 2 deferred it), so
    there is nothing real to populate this with until Phase 4 resolves
    edition identity. The field exists now because `EvidenceAnchor`
    itself is the real consumer that will need it then; that's
    different from adding an unused field to the stable, heavily used
    `Media` dataclass itself.
    """

    media_id: UUID
    stream: str | None = None
    start_seconds: float | None = None
    end_seconds: float | None = None
    spatial_region: tuple[float, float, float, float] | None = None
    asset_ref: str | None = None
    edition_id: str | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if (
            self.start_seconds is not None
            and self.end_seconds is not None
            and self.end_seconds < self.start_seconds
        ):
            raise ValueError(
                f"end_seconds ({self.end_seconds}) must not precede "
                f"start_seconds ({self.start_seconds})"
            )
        if self.spatial_region is not None and len(self.spatial_region) != 4:
            raise ValueError(
                "spatial_region must be a (x, y, width, height) 4-tuple, "
                f"got {len(self.spatial_region)} values"
            )
