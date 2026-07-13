"""
SceneForge

The Open Framework for Narrative Intelligence.
"""

from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import (
    DuplicateProviderError,
    InvalidMetadataError,
    InvalidNameError,
    ProcessingCancelledError,
    ProviderNotFoundError,
    SceneForgeError,
)
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.provider import Provider
from sceneforge.core.registry import Registry
from sceneforge.runtime.processing_context import ProcessingContext

__version__ = "0.1.0"

__all__ = [
    "Artifact",
    "ArtifactKind",
    "Capability",
    "DuplicateProviderError",
    "InvalidMetadataError",
    "InvalidNameError",
    "Pipeline",
    "ProcessingCancelledError",
    "Provider",
    "ProcessingContext",
    "ProviderNotFoundError",
    "Registry",
    "SceneForgeError",
]
