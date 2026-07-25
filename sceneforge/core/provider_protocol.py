"""
SceneForge Provider Protocol

Structural (duck-typed) contract for processing media into artifacts.

This used to declare only `run()`, even though Pipeline (and every
provider actually shipped in `sceneforge.contrib`) also depends on
`name`, `version`, and `capabilities` -- so a provider that only
satisfied the *documented* Protocol would have crashed the moment
Pipeline touched `.capabilities`. mypy --strict didn't catch this
before because Pipeline was never actually type-checked against real
callers exercising those attributes; it does now.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.media.base import Media


@runtime_checkable
class Provider(Protocol):
    """
    Protocol for processing media into artifacts.

    Any class exposing `name`, `version`, `capabilities`, and a
    `run()` method returning `list[Artifact]` participates.
    Implementations don't need to inherit from this protocol -- see
    `tests/core/test_pipeline.py::IdentityProvider` for a structural
    (non-ABC) example.
    """

    @property
    def name(self) -> str:
        """Return the provider name."""
        ...

    @property
    def version(self) -> str:
        """Return the provider version."""
        ...

    @property
    def capabilities(self) -> frozenset[Capability]:
        """Return the capabilities this provider implements."""
        ...

    @property
    def execution_fingerprint(self) -> str:
        """
        Return a deterministic string capturing configuration that
        affects this provider's output, beyond name and version.

        Folded into `content_key()` (ADR-0024 Phase 0 item 2). A
        provider with no such configuration can return `""`.
        """
        ...

    def run(self, media: Media) -> list[Artifact[Any]]:
        """Process media and return artifacts."""
        ...
