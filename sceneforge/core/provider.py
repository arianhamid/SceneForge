"""
SceneForge Provider

Base class for all providers that interact with external AI systems.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability

if TYPE_CHECKING:
    from sceneforge.media.base import Media


class Provider(ABC):
    """
    Abstract base class for all SceneForge providers.

    Providers communicate with external AI systems and produce
    artifacts. They should never contain knowledge construction
    or application logic.

    The run() method is the contract: accept Media, return list[Artifact].
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Return the provider version."""

    @property
    @abstractmethod
    def capabilities(self) -> frozenset[Capability]:
        """Return the capabilities this provider implements."""

    @property
    def execution_fingerprint(self) -> str:
        """
        Return a deterministic string capturing configuration that
        affects this provider's output, beyond name and version.

        Folded into `content_key()` (ADR-0024 Phase 0 item 2) so two
        differently configured instances of the same provider version
        do not collide in the cache. Most providers have no
        configuration surface that changes output and can rely on this
        default (empty string, contributes nothing to the key).
        Override it when the provider accepts constructor-time
        configuration that changes what `run()` produces --
        `WhisperTranscribeProvider`'s `transcribe_kwargs` is the
        concrete case that motivated this (the 2026-07-22
        implementation review reproduced two differently configured
        instances colliding under the old key).
        """
        return ""

    @abstractmethod
    def run(self, media: Media) -> list[Artifact[Any]]:
        """Process media and return artifacts."""
