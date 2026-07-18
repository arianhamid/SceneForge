"""
SceneForge OpenCV Contrib Package

SceneForge's fourth real (non-stub) integration, and second capability
domain (image, after video/audio): `Capability.FACE_DETECTION` via
OpenCV's bundled Haar cascade classifier, plus `OpenCVImageEnricher`
for real image dimensions (closing a gap that's existed for `ImageMedia`
since Sprint 1 -- `FFprobeEnricher` fixed the equivalent problem for
video back in Sprint 2, images were never done).

Like `sceneforge.contrib.scenedetect`, this needs no dependency
injection and no network access: the classifier weights ship inside
the `opencv-python`/`opencv-python-headless` package itself.
"""

from sceneforge.contrib.opencv.face_detection_artifact import FaceDetectionArtifact
from sceneforge.contrib.opencv.face_detection_provider import (
    OpenCVFaceDetectionProvider,
)
from sceneforge.contrib.opencv.image_probe_enricher import OpenCVImageEnricher

__all__ = [
    "FaceDetectionArtifact",
    "OpenCVFaceDetectionProvider",
    "OpenCVImageEnricher",
]
