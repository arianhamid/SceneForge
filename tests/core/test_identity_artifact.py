from uuid import UUID

from sceneforge.core.artifact import ArtifactKind
from sceneforge.core.identity_artifact import IdentityArtifact


def test_identity_artifact_construction():
    artifact = IdentityArtifact(
        media_id=UUID("12345678-1234-5678-1234-567812345678"),
        provider="identity",
    )

    assert artifact.media_id == UUID("12345678-1234-5678-1234-567812345678")
    assert artifact.provider == "identity"


def test_identity_artifact_kind():
    artifact = IdentityArtifact(
        media_id=UUID("12345678-1234-5678-1234-567812345678"),
        provider="identity",
    )

    assert artifact.kind == ArtifactKind.ARTIFACT


def test_identity_artifact_is_immutable():
    import pytest

    artifact = IdentityArtifact(
        media_id=UUID("12345678-1234-5678-1234-567812345678"),
        provider="identity",
    )

    with pytest.raises(AttributeError):
        artifact.provider = "changed"  # type: ignore[misc]


def test_identity_artifact_has_id():
    artifact = IdentityArtifact(
        media_id=UUID("12345678-1234-5678-1234-567812345678"),
        provider="identity",
    )

    assert artifact.id is not None
    assert len(str(artifact.id)) == 36
