"""
SceneForge Artifact

Defines the immutable base class for every observation flowing
through the SceneForge framework.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Generic, Mapping, TypeVar
from uuid import UUID, uuid4

T = TypeVar("T")


class ArtifactKind(StrEnum):
    """Vocabulary of artifact types. Prevents string typos."""

    ARTIFACT = "artifact"
    FRAME = "frame"
    TRANSCRIPT = "transcript"
    SCENE_CUT = "scene_cut"
    CAPTION = "caption"
    OCR = "ocr"
    EMBEDDING = "embedding"
    FACE_DETECTION = "face_detection"
    OBJECT_DETECTION = "object_detection"
    AUDIO_SEGMENT = "audio_segment"


@dataclass(frozen=True, slots=True)
class Artifact(ABC, Generic[T]):
    """
    Immutable base class for every SceneForge artifact.

    Artifacts represent observations produced by providers.
    They should never contain reasoning or application-specific
    logic.

    Type parameter T represents the payload type:
        Artifact[np.ndarray]  # image data
        Artifact[str]         # text
        Artifact[dict]        # structured data
    """

    id: UUID = field(default_factory=uuid4)

    kind: ArtifactKind = ArtifactKind.ARTIFACT

    provider: str = "unknown"

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    payload: T = None  # type: ignore[assignment]

    metadata: Mapping[str, Any] = field(default_factory=dict)

    parents: tuple[UUID, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(dict(self.metadata)),
        )
