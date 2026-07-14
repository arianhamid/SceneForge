import pytest

from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import (
    DuplicateProviderError,
    ProviderNotFoundError,
)
from sceneforge.core.provider import Provider
from sceneforge.core.registry import Registry


class DummyProvider(Provider):

    @property
    def name(self):
        return "dummy"

    @property
    def version(self):
        return "1.0.0"

    @property
    def capabilities(self):
        return frozenset({Capability.CAPTION})

    def run(self, media):
        return []


def test_register_provider():
    registry = Registry()
    provider = DummyProvider()

    registry.register(provider)

    assert len(registry) == 1


def test_register_duplicate_raises():
    registry = Registry()
    provider = DummyProvider()

    registry.register(provider)

    with pytest.raises(DuplicateProviderError):
        registry.register(provider)


def test_get_provider():
    registry = Registry()
    provider = DummyProvider()

    registry.register(provider)

    assert registry.get("dummy") is provider


def test_get_nonexistent_raises():
    registry = Registry()

    with pytest.raises(ProviderNotFoundError):
        registry.get("nonexistent")


def test_unregister_provider():
    registry = Registry()
    provider = DummyProvider()

    registry.register(provider)
    registry.unregister("dummy")

    assert len(registry) == 0


def test_unregister_nonexistent_raises():
    registry = Registry()

    with pytest.raises(ProviderNotFoundError):
        registry.unregister("nonexistent")


def test_contains():
    registry = Registry()
    provider = DummyProvider()

    registry.register(provider)

    assert registry.contains("dummy") is True
    assert registry.contains("nonexistent") is False


def test_clear():
    registry = Registry()
    provider = DummyProvider()

    registry.register(provider)
    registry.clear()

    assert len(registry) == 0


def test_providers():
    registry = Registry()
    provider = DummyProvider()

    registry.register(provider)

    assert provider in registry.providers()


def test_find_by_capability():
    registry = Registry()
    provider = DummyProvider()

    registry.register(provider)

    providers = registry.by_capability(Capability.CAPTION)

    assert provider in providers


def test_contains_method():
    registry = Registry()
    provider = DummyProvider()

    assert "dummy" not in registry

    registry.register(provider)

    assert "dummy" in registry
    assert "nonexistent" not in registry
