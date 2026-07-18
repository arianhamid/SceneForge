from sceneforge.core.artifact import Artifact, ArtifactKind


class DummyArtifact(Artifact):
    pass


def test_artifact_defaults():
    artifact = DummyArtifact()

    assert artifact.kind == ArtifactKind.ARTIFACT
    assert artifact.provider == "unknown"
    assert artifact.parents == ()


def test_artifact_is_immutable():
    artifact = DummyArtifact(provider="test")

    try:
        artifact.kind = ArtifactKind.FRAME  # type: ignore[misc]
        raise AssertionError("Artifact should be immutable")
    except AttributeError:
        pass


def test_artifact_has_uuid():
    artifact = DummyArtifact()

    assert artifact.id is not None
    assert len(str(artifact.id)) == 36


def test_artifact_has_timestamp():
    artifact = DummyArtifact()

    assert artifact.created_at is not None


def test_artifact_metadata_is_immutable():
    artifact = DummyArtifact(metadata={"key": "value"})

    try:
        artifact.metadata["new_key"] = "new_value"  # type: ignore[index]
        raise AssertionError("Metadata should be immutable")
    except TypeError:
        pass
