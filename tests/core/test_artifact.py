"""Compatibility tests for the stable Artifact base class."""

from abc import ABCMeta

from sceneforge.core.artifact import Artifact


def test_artifact_retains_abc_marker() -> None:
    assert isinstance(Artifact, ABCMeta)


def test_artifact_remains_directly_instantiable() -> None:
    assert Artifact().payload is None
