"""
SceneForge Media Base

Immutable base class for all media types.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
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

    def evolve(
        self, *, metadata: dict[str, Any] | None = None, **changes: Any
    ) -> Media:
        """
        Return a new instance of this Media's concrete type with the
        given fields replaced.

        Media is immutable by design, so nothing may ever be mutated
        in place. This is the *sanctioned* path for turning
        placeholder metadata produced by a cheap loader (e.g.
        ``duration=0.0, codec="unknown"``) into authoritative metadata
        discovered by a :class:`~sceneforge.core.enrichment.MediaEnricher`.

        ``metadata`` is merged into the existing metadata mapping
        rather than replacing it outright, so enrichers don't need to
        know about metadata a loader (or an earlier enricher) already
        set.

        Args:
            metadata: Keys to merge into the existing metadata.
            **changes: Any other dataclass field to replace (e.g.
                ``fps=24.0, codec="h264"`` on a ``VideoMedia``).

        Returns:
            A new, immutable instance of the same concrete type.
        """
        if metadata is not None:
            merged = dict(self.metadata)
            merged.update(metadata)
            changes["metadata"] = merged
        return replace(self, **changes)
