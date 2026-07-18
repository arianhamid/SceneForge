"""
SceneForge Capability Registry

Registers which media types each capability supports.

This used to be a module-level mutable dict (`_CAPABILITY_MEDIA_MAP`)
shared by every Pipeline in the process, with a class-level "have I
registered yet" flag bolted onto Pipeline to fake a one-time init.
That's hidden, shared, mutable state -- the framework's own
ARCHITECTURAL_PRINCIPLES.md rules this out ("no hidden state").

CapabilityRegistry is now a plain object. Pipeline takes one in its
constructor (defaulting to a shared, pre-populated instance for
convenience), so:
  * two Pipelines in the same process can use two different registries
    without stepping on each other (e.g. isolated tests, a sandboxed
    plugin's custom capabilities)
  * nothing has to remember whether "registration" already happened
"""

from __future__ import annotations

from sceneforge.core.capability import Capability
from sceneforge.media.base import Media


class CapabilityRegistry:
    """Maps each Capability to the Media types it can operate on."""

    def __init__(self) -> None:
        self._map: dict[Capability, set[type[Media]]] = {}

    def register(
        self,
        capability: Capability,
        media_types: set[type[Media]],
    ) -> None:
        """Register (or replace) which media types a capability supports."""
        self._map[capability] = set(media_types)

    def extend(
        self,
        capability: Capability,
        media_types: set[type[Media]],
    ) -> None:
        """Add media types to a capability's existing support set."""
        self._map.setdefault(capability, set()).update(media_types)

    def supported_media_types(self, capability: Capability) -> set[type[Media]]:
        """Return the media types registered for a capability (empty set if none)."""
        return set(self._map.get(capability, set()))

    def is_compatible(self, capability: Capability, media_type: type[Media]) -> bool:
        """
        Return whether ``media_type`` is compatible with ``capability``.

        A capability with no registered media types is treated as
        "unconstrained" (compatible with anything) -- this matches the
        historical Pipeline behavior of skipping validation for
        capabilities nobody has described yet, rather than silently
        rejecting everything.
        """
        supported = self._map.get(capability)
        if not supported:
            return True
        return media_type in supported

    def __contains__(self, capability: Capability) -> bool:
        return capability in self._map

    def __len__(self) -> int:
        return len(self._map)


def build_default_capability_registry() -> CapabilityRegistry:
    """Build a fresh registry pre-populated with SceneForge's built-in capabilities."""
    from sceneforge.media.audio import AudioMedia
    from sceneforge.media.image import ImageMedia
    from sceneforge.media.video import VideoMedia

    registry = CapabilityRegistry()

    # Image/Video capabilities
    registry.register(Capability.CAPTION, {ImageMedia, VideoMedia})
    registry.register(Capability.OCR, {ImageMedia, VideoMedia})
    registry.register(Capability.FACE_DETECTION, {ImageMedia, VideoMedia})
    registry.register(Capability.OBJECT_DETECTION, {ImageMedia, VideoMedia})
    registry.register(Capability.EMBEDDING, {ImageMedia, VideoMedia, AudioMedia})

    # Video-only capabilities
    registry.register(Capability.DETECT_SCENES, {VideoMedia})
    registry.register(Capability.FRAME_EXTRACTION, {VideoMedia})

    # Audio capabilities
    registry.register(Capability.TRANSCRIBE, {AudioMedia, VideoMedia})
    registry.register(Capability.AUDIO_ANALYSIS, {AudioMedia})

    return registry


# A shared, pre-populated registry used as Pipeline's default so callers
# who don't care about isolation don't have to construct one themselves.
# Anyone who *does* care (tests, plugins with custom capabilities) should
# construct their own CapabilityRegistry() and pass it explicitly.
DEFAULT_CAPABILITY_REGISTRY = build_default_capability_registry()
