from typing import Protocol

from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.provider_protocol import Provider
from sceneforge.media.base import Media


def test_provider_is_protocol():
    assert issubclass(Provider, Protocol)


def test_provider_has_run_method():
    assert hasattr(Provider, "run")


def test_provider_is_abstract():
    import pytest

    with pytest.raises(TypeError):
        Provider()


def test_runtime_checkable():
    """
    A class must implement the *whole* structural contract -- name,
    version, capabilities, execution_fingerprint, and run() -- to
    satisfy Provider, since that's everything Pipeline actually
    touches. A run()-only class is not a usable Provider even though
    it "looks" like one; see test_run_only_class_is_not_a_provider
    below for the failure mode this protects against.
    """

    class ConcreteProvider:
        @property
        def name(self) -> str:
            return "concrete"

        @property
        def version(self) -> str:
            return "1.0.0"

        @property
        def capabilities(self) -> frozenset[Capability]:
            return frozenset()

        @property
        def execution_fingerprint(self) -> str:
            return ""

        def run(self, media: Media) -> list[Artifact]:
            return []

    assert isinstance(ConcreteProvider(), Provider)


def test_run_only_class_is_not_a_provider():
    """
    A class with only run() does not satisfy Provider -- Pipeline
    would crash on `.capabilities` the moment it tried to validate
    media against it, so the Protocol must not claim otherwise.
    """

    class RunOnly:
        def run(self, media: Media) -> list[Artifact]:
            return []

    assert not isinstance(RunOnly(), Provider)
