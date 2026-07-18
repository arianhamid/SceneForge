"""
SceneForge Knowledge Entities

An Entity is a reusable concept derived from one or more Artifacts --
see docs/architecture/DOMAIN_MODEL.md's "Entity" section. Where an
Artifact is a single provider's immutable observation, an Entity is a
Knowledge Builder's synthesis across possibly many artifacts, possibly
from several different providers.

Entities follow the same immutability discipline as Artifact and
Media: nothing is ever mutated in place. `parents` records the
Artifact ids an Entity was built from, so a Knowledge Builder's output
is always traceable back to the raw observations behind it -- the same
way `Artifact.parents` traces a correction back to what it corrected.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Generic, TypeVar
from uuid import UUID, uuid4

T = TypeVar("T")


class EntityKind(StrEnum):
    """Vocabulary of entity types. Prevents string typos."""

    ENTITY = "entity"
    SCENE = "scene"
    CHARACTER = "character"
    LOCATION = "location"
    CHAPTER = "chapter"
    EVENT = "event"
    DIALOGUE = "dialogue"
    RELATIONSHIP = "relationship"


@dataclass(frozen=True, slots=True)
class Entity(Generic[T]):
    """
    Immutable base class for every SceneForge knowledge entity.

    Entities represent concepts synthesized by a Knowledge Builder
    from one or more Artifacts. They should never contain
    application-specific logic, and a Knowledge Builder must never
    mutate the Artifacts it reads to produce one.
    """

    id: UUID = field(default_factory=uuid4)

    kind: EntityKind = EntityKind.ENTITY

    builder: str = "unknown"

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    payload: T = None  # type: ignore[assignment]

    metadata: Mapping[str, Any] = field(default_factory=dict)

    parents: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )
