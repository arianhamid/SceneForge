"""
Identity Provider Tests.
"""

from sceneforge.contrib.identity import IdentityProvider
from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.pipeline import Pipeline
from sceneforge.media.image import ImageMedia


def test_identity_provider_name():
    provider = IdentityProvider()
    assert provider.name == "identity"


def test_identity_provider_version():
    provider = IdentityProvider()
    assert provider.version == "1.0.0"


def test_identity_provider_capabilities():
    provider = IdentityProvider()
    assert provider.capabilities == frozenset()


def test_identity_provider_returns_unchanged():
    provider = IdentityProvider()
    artifact = Artifact(kind=ArtifactKind.FRAME, provider="test")

    result = list(provider.process([artifact]))

    assert len(result) == 1
    assert result[0] is artifact


def test_identity_provider_empty():
    provider = IdentityProvider()
    result = list(provider.process([]))
    assert result == []


def test_identity_in_pipeline():
    provider = IdentityProvider()
    pipeline = Pipeline(provider=provider)

    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")
    result = list(pipeline.run(media))

    assert len(result) == 1
    assert result[0].provider == "identity"
