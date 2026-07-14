"""
SceneForge Pipeline Tests.
"""

from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.capability import Capability
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.provider import Provider
from sceneforge.media.image import ImageMedia
from sceneforge.media.base import Media


class EchoProvider(Provider):
    """Provider that returns artifacts unchanged. Subclasses Provider ABC."""

    @property
    def name(self) -> str:
        return "echo"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset()

    def run(self, media: Media):
        """Process media and return artifacts."""
        return [
            Artifact(kind=ArtifactKind.ARTIFACT, provider=self.name)
        ]


class IdentityProvider:
    """Provider that returns artifacts unchanged. Structural (no ABC inheritance)."""

    @property
    def name(self) -> str:
        return "identity"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self):
        return frozenset()

    def run(self, media):
        """Process media and return artifacts."""
        return [
            Artifact(kind=ArtifactKind.ARTIFACT, provider=self.name)
        ]


class EmptyProvider:
    """Provider that returns no artifacts."""

    @property
    def name(self) -> str:
        return "empty"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self):
        return frozenset()

    def run(self, media):
        """Process media and return no artifacts."""
        return []


def test_pipeline_accepts_media():
    """Pipeline.run() should accept a Media object."""
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")
    pipeline = Pipeline(provider=EchoProvider())
    result = list(pipeline.run(media))
    assert len(result) == 1


def test_pipeline_returns_artifacts():
    """Pipeline.run() should return artifacts from the provider."""
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")
    pipeline = Pipeline(provider=EchoProvider())
    result = list(pipeline.run(media))
    assert all(isinstance(a, Artifact) for a in result)


def test_pipeline_single_provider():
    """Pipeline should work with a single provider."""
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")
    pipeline = Pipeline(provider=IdentityProvider())
    result = list(pipeline.run(media))
    assert len(result) == 1


def test_pipeline_empty():
    """Pipeline should handle empty media gracefully."""
    media = ImageMedia(name="empty.jpg", width=0, height=0, fmt="JPEG")
    pipeline = Pipeline(provider=EmptyProvider())
    result = list(pipeline.run(media))
    assert result == []


def test_pipeline_abc_subclass():
    """Pipeline should work with providers that subclass Provider ABC."""
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")
    pipeline = Pipeline(provider=EchoProvider())
    result = list(pipeline.run(media))
    assert len(result) == 1
    assert result[0].provider == "echo"


def test_pipeline_structural_provider():
    """Pipeline should work with structural providers (duck typing)."""
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")
    pipeline = Pipeline(provider=IdentityProvider())
    result = list(pipeline.run(media))
    assert len(result) == 1
    assert result[0].provider == "identity"
