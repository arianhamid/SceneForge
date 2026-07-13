from sceneforge.core.artifact import Artifact


class DummyArtifact(Artifact):
    pass


def test_artifact_defaults():
    artifact = DummyArtifact()

    assert artifact.type == "artifact"
    assert artifact.provider == "unknown"
    assert artifact.parents == ()