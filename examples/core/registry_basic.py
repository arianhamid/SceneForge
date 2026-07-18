"""
SceneForge Registry: query by capability

Demonstrates Registry.by_capability() -- finding every registered
provider that implements a given capability, using two of the three
real providers shipped in sceneforge.contrib (whisper is skipped here
since it needs a real model instance; see
docs/specifications/PROVIDER_SPEC.md's whisper example for that).
"""

from sceneforge.contrib.ffmpeg import FFmpegFrameExtractionProvider
from sceneforge.contrib.scenedetect import PySceneDetectProvider
from sceneforge.core.capability import Capability
from sceneforge.core.registry import Registry

registry = Registry()
registry.register(FFmpegFrameExtractionProvider())
registry.register(PySceneDetectProvider())

scene_detectors = registry.by_capability(Capability.DETECT_SCENES)
for provider in scene_detectors:
    print(f"{provider.name} implements DETECT_SCENES")

print(f"\n{len(registry)} providers registered total")
