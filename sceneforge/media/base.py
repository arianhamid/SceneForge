"""
SceneForge Media Base

Immutable base class for all media types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Media:
    """
    Immutable base class for media objects.

    Media objects represent media resources (images, videos, audio)
    without containing any decoding logic.
    """

    name: str

    id: UUID = field(default_factory=uuid4)

    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )
