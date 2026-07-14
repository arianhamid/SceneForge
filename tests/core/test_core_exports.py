from sceneforge.core import (
    IdentityArtifact,
    InvalidMediaError,
    ProviderError,
    ProviderNotFoundError,
    ProviderProtocol,
)


def test_all_core_types_exported():
    assert ProviderProtocol is not None
    assert IdentityArtifact is not None
    assert ProviderError is not None
    assert ProviderNotFoundError is not None
    assert InvalidMediaError is not None
