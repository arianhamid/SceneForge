"""
Runtime processing context.

A ProcessingContext carries execution state throughout a
SceneForge processing session.

Unlike Artifacts, a ProcessingContext is mutable and exists
only for the lifetime of a pipeline execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ProcessingContext:
    """
    Runtime information shared between providers.

    This object intentionally contains no business logic.
    """

    request_id: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    cancelled: bool = False

    def cancel(self) -> None:
        self.cancelled = True
