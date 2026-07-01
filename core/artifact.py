artifact = FrameArtifact(
    timestamp=12.35,
    provider="opencv",
    path="frames/000124.jpg",
)

artifact.id

artifact.provider

artifact.timestamp

artifact.metadata

artifact.to_json()

artifact.from_json()

artifact.hash()

artifact.validate()