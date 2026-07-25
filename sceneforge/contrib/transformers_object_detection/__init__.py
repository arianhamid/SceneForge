"""
SceneForge Transformers Object Detection Contrib Package

Real implementation of `Capability.OBJECT_DETECTION` via Hugging Face
`transformers`, with the pipeline injected rather than constructed
internally -- see `provider.py`'s module docstring. This is the
second real provider feeding the Facts rung
(`sceneforge.contrib.transformers_caption` was the first), built to
test whether `FactExtractionBuilder`'s shape generalizes.
"""

from sceneforge.contrib.transformers_object_detection.object_detection_artifact import (
    ObjectDetectionArtifact,
)
from sceneforge.contrib.transformers_object_detection.provider import (
    ObjectDetectionPipelineProtocol,
    TransformersObjectDetectionProvider,
)

__all__ = [
    "ObjectDetectionArtifact",
    "ObjectDetectionPipelineProtocol",
    "TransformersObjectDetectionProvider",
]
