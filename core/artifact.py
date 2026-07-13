"""
SceneForge Artifact

Defines the immutable base class for every observation flowing
through the SceneForge framework.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Artifact(ABC):
    """
    Immutable base class for every SceneForge artifact.

    Artifacts represent observations produced by providers.
    They should never contain reasoning or application-specific
    logic.
    """

    id: UUID = field(default_factory=uuid4)

    type: str = "artifact"

    provider: str = "unknown"

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    payload: Any = None

    metadata: Mapping[str, Any] = field(default_factory=dict)

    parents: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )