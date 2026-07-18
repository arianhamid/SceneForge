"""Tests for CapabilityRegistry."""

from sceneforge.core.capability import Capability
from sceneforge.core.capability_registry import (
    CapabilityRegistry,
    build_default_capability_registry,
)
from sceneforge.media.audio import AudioMedia
from sceneforge.media.image import ImageMedia
from sceneforge.media.video import VideoMedia


def test_default_registry_covers_built_in_capabilities():
    """The default registry should cover every built-in capability."""
    registry = build_default_capability_registry()

    assert ImageMedia in registry.supported_media_types(Capability.CAPTION)
    assert AudioMedia in registry.supported_media_types(Capability.TRANSCRIBE)
    assert VideoMedia in registry.supported_media_types(Capability.DETECT_SCENES)


def test_registry_is_compatible():
    registry = build_default_capability_registry()

    assert registry.is_compatible(Capability.CAPTION, ImageMedia)
    assert not registry.is_compatible(Capability.DETECT_SCENES, AudioMedia)


def test_unregistered_capability_is_unconstrained():
    """A capability nobody registered types for should accept anything."""
    registry = CapabilityRegistry()

    assert registry.is_compatible(Capability.CAPTION, ImageMedia)
    assert registry.is_compatible(Capability.CAPTION, AudioMedia)


def test_two_registries_are_isolated():
    """Two CapabilityRegistry instances must never share state."""
    registry_a = CapabilityRegistry()
    registry_b = CapabilityRegistry()

    registry_a.register(Capability.CAPTION, {ImageMedia})

    assert Capability.CAPTION in registry_a
    assert Capability.CAPTION not in registry_b


def test_extend_adds_without_replacing():
    registry = CapabilityRegistry()
    registry.register(Capability.CAPTION, {ImageMedia})
    registry.extend(Capability.CAPTION, {VideoMedia})

    supported = registry.supported_media_types(Capability.CAPTION)
    assert supported == {ImageMedia, VideoMedia}


def test_register_replaces_extend_adds():
    registry = CapabilityRegistry()
    registry.register(Capability.CAPTION, {ImageMedia})
    registry.register(Capability.CAPTION, {VideoMedia})

    assert registry.supported_media_types(Capability.CAPTION) == {VideoMedia}


def test_len_and_contains():
    registry = CapabilityRegistry()
    assert len(registry) == 0

    registry.register(Capability.CAPTION, {ImageMedia})
    assert len(registry) == 1
    assert Capability.CAPTION in registry
    assert Capability.OCR not in registry
