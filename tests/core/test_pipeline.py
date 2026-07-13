"""
SceneForge Pipeline Tests.
"""

from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.provider import Provider
from sceneforge.runtime import ProcessingContext


class EchoProvider(Provider):
    """Provider that returns artifacts unchanged."""

    @property
    def name(self) -> str:
        return "echo"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self):
        return frozenset()

    def process(self, artifacts, *, context=None):
        return artifacts


class DoublingProvider(Provider):
    """Provider that duplicates each artifact."""

    @property
    def name(self) -> str:
        return "doubler"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self):
        return frozenset()

    def process(self, artifacts, *, context=None):
        result = []
        for artifact in artifacts:
            result.append(artifact)
            result.append(artifact)
        return result


def test_pipeline_empty():
    pipeline = Pipeline([EchoProvider()])
    assert list(pipeline.run([])) == []


def test_pipeline_echo():
    artifact = Artifact(kind=ArtifactKind.FRAME, provider="test")
    pipeline = Pipeline([EchoProvider()])
    result = list(pipeline.run([artifact]))
    assert len(result) == 1
    assert result[0] is artifact


def test_pipeline_doubler():
    artifact = Artifact(kind=ArtifactKind.FRAME, provider="test")
    pipeline = Pipeline([DoublingProvider()])
    result = list(pipeline.run([artifact]))
    assert len(result) == 2


def test_pipeline_chain():
    artifact = Artifact(kind=ArtifactKind.FRAME, provider="test")
    pipeline = Pipeline([EchoProvider(), DoublingProvider()])
    result = list(pipeline.run([artifact]))
    assert len(result) == 2


def test_pipeline_with_context():
    context = ProcessingContext(request_id="test-123")
    pipeline = Pipeline([EchoProvider()])
    result = list(pipeline.run([], context=context))
    assert result == []
