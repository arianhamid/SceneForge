"""
SceneForge Pipeline Example

Demonstrates the orchestration boundary for processing media.
"""

from sceneforge.contrib.identity import IdentityProvider
from sceneforge.core.pipeline import Pipeline
from sceneforge.media.image import ImageMedia

# Create media
image = ImageMedia(name="photo.jpg", width=1920, height=1080, fmt="JPEG")

# Create pipeline with provider
pipeline = Pipeline(provider=IdentityProvider())

# Process media
artifacts = pipeline.run(image)

# Inspect results
for artifact in artifacts:
    print(f"Artifact: {artifact.kind}, Provider: {artifact.provider}")
