"""
SceneForge Transformers Caption Contrib Package

Real implementation of `Capability.CAPTION` via Hugging Face
`transformers`, with the pipeline injected rather than constructed
internally -- see `provider.py`'s module docstring for why. This is
Phase 1 of ADR-0024's roadmap: the captioning provider that unblocks
the "Facts" rung of the Understanding Ladder (ADR-0021).
"""

from sceneforge.contrib.transformers_caption.caption_artifact import CaptionArtifact
from sceneforge.contrib.transformers_caption.provider import (
    ImageTextToTextPipelineProtocol,
    TransformersCaptionProvider,
)

__all__ = [
    "CaptionArtifact",
    "ImageTextToTextPipelineProtocol",
    "TransformersCaptionProvider",
]
