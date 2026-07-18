"""
Provider Contract Tests

Reusable test suite that every provider must pass.
"""


from sceneforge.core.artifact import Artifact
from sceneforge.core.provider_protocol import Provider
from sceneforge.media.base import Media


def provider_contract(provider: Provider, media: Media) -> None:
    """
    Run contract tests for a provider.

    Args:
        provider: The provider to test.
        media: Media to process.

    Raises:
        AssertionError: If provider fails contract tests.
    """
    # Test 1: Provider has required properties
    assert hasattr(provider, 'name')
    assert isinstance(provider.name, str)
    assert len(provider.name) > 0

    assert hasattr(provider, 'version')
    assert isinstance(provider.version, str)
    assert len(provider.version) > 0

    assert hasattr(provider, 'capabilities')
    assert isinstance(provider.capabilities, frozenset)

    # Test 2: Provider has run method
    assert hasattr(provider, 'run')
    assert callable(provider.run)

    # Test 3: run() returns list of Artifacts
    result = provider.run(media)
    assert isinstance(result, list)
    assert len(result) >= 0

    for artifact in result:
        assert isinstance(artifact, Artifact)
        assert hasattr(artifact, 'id')
        assert hasattr(artifact, 'provider')
        assert artifact.provider == provider.name
