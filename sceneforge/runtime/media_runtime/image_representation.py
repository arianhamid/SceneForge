"""
SceneForge Image Representation

Execution-time representation of image data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class ImageRepresentation:
    """
    Execution-time representation of image data.

    This is NOT a domain object. It exists only during processing.
    Media remains immutable; this holds the decoded pixels.
    """

    media_id: UUID
    width: int
    height: int
    dtype: str  # e.g., "uint8", "float32"
    shape: tuple[int, ...]  # e.g., (height, width, 3)
    data: Any  # np.ndarray or similar

    id: UUID = field(default_factory=uuid4)

    @property
    def pixel_count(self) -> int:
        """Total number of pixels."""
        return self.width * self.height

    @property
    def channels(self) -> int:
        """Number of color channels."""
        return self.shape[2] if len(self.shape) > 2 else 1
