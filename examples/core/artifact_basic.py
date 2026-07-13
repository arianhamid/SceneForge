from sceneforge.core.artifact import Artifact


class CaptionArtifact(Artifact):
    pass


artifact = CaptionArtifact(
    provider="joycaption",
    payload="A man walks into a room."
)

print(artifact)