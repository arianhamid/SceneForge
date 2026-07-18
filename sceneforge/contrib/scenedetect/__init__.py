"""
SceneForge PySceneDetect Contrib Package

SceneForge's second real (non-stub) capability implementation:
`Capability.DETECT_SCENES` via the `scenedetect` library. Unlike a
transcription or captioning provider, scene detection needs no model
weights and no network access -- it's pure content-based frame
analysis -- so this package is fully integration-tested against a
real generated video, the same way `sceneforge.contrib.ffmpeg` is.
"""

from sceneforge.contrib.scenedetect.provider import PySceneDetectProvider
from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact

__all__ = ["PySceneDetectProvider", "SceneCutArtifact"]
