"""
SceneForge Pipeline Tests.
"""

import pytest
from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import IncompatibleMediaError
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.provider import Provider
from sceneforge.media.image import ImageMedia
from sceneforge.media.audio import AudioMedia
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


def test_pipeline_rejects_incompatible_media():
    """Pipeline should reject media incompatible with provider capabilities."""
    # ImageProvider that only works with images
    class ImageProvider(Provider):
        @property
        def name(self) -> str:
            return "image_only"
        
        @property
        def version(self) -> str:
            return "1.0.0"
        
        @property
        def capabilities(self) -> frozenset[Capability]:
            return frozenset({Capability.CAPTION})
        
        def run(self, media: Media):
            return [Artifact(kind=ArtifactKind.CAPTION, provider=self.name)]
    
    # AudioMedia should be rejected by ImageProvider
    audio = AudioMedia(
        name="sound.wav",
        duration=30.0,
        sample_rate=44100,
        channels=2
    )
    
    pipeline = Pipeline(provider=ImageProvider())
    
    with pytest.raises(IncompatibleMediaError) as exc_info:
        pipeline.run(audio)
    
    assert exc_info.value.provider == "image_only"
    assert exc_info.value.media_type == "AudioMedia"


def test_pipeline_accepts_compatible_media():
    """Pipeline should accept media compatible with provider capabilities."""
    # ImageProvider that only works with images
    class ImageProvider(Provider):
        @property
        def name(self) -> str:
            return "image_only"
        
        @property
        def version(self) -> str:
            return "1.0.0"
        
        @property
        def capabilities(self) -> frozenset[Capability]:
            return frozenset({Capability.CAPTION})
        
        def run(self, media: Media):
            return [Artifact(kind=ArtifactKind.CAPTION, provider=self.name)]
    
    # ImageMedia should be accepted by ImageProvider
    image = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")
    
    pipeline = Pipeline(provider=ImageProvider())
    result = pipeline.run(image)
    
    assert len(result) == 1
    assert result[0].kind == ArtifactKind.CAPTION


def test_pipeline_no_capabilities_accepts_all():
    """Pipeline should accept all media when provider has no capabilities."""
    # Provider with no capabilities
    class GenericProvider(Provider):
        @property
        def name(self) -> str:
            return "generic"
        
        @property
        def version(self) -> str:
            return "1.0.0"
        
        @property
        def capabilities(self) -> frozenset[Capability]:
            return frozenset()
        
        def run(self, media: Media):
            return [Artifact(kind=ArtifactKind.ARTIFACT, provider=self.name)]
    
    # Any media should be accepted
    audio = AudioMedia(
        name="sound.wav",
        duration=30.0,
        sample_rate=44100,
        channels=2
    )
    
    pipeline = Pipeline(provider=GenericProvider())
    result = pipeline.run(audio)
    
    assert len(result) == 1
