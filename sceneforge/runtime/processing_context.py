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

from sceneforge.core.exceptions import ProcessingCancelledError


@dataclass(slots=True)
class ProcessingContext:
    """
    Runtime information shared between providers.

    Providers can call ensure_running() to check if execution
    should continue, or raise if cancelled.
    """

    request_id: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    _cancelled: bool = field(default=False, init=False, repr=False)

    @property
    def cancelled(self) -> bool:
        return self._cancelled

    def cancel(self) -> None:
        self._cancelled = True

    def ensure_running(self) -> None:
        if self._cancelled:
            raise ProcessingCancelledError()
