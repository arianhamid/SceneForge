"""
SceneForge Core

The foundational layer of the SceneForge framework.
"""

from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.capability import Capability
from sceneforge.core.capability_registry import register_default_capabilities
from sceneforge.core.exceptions import (
    DuplicateProviderError,
    IncompatibleMediaError,
    InvalidMediaError,
    InvalidMetadataError,
    InvalidNameError,
    ProcessingCancelledError,
    ProviderError,
    ProviderNotFoundError,
    SceneForgeError,
)
from sceneforge.core.identity_artifact import IdentityArtifact
from sceneforge.core.pipeline import Pipeline
from sceneforge.core.provider import Provider
from sceneforge.core.provider_protocol import Provider as ProviderProtocol
from sceneforge.core.registry import Registry

__all__ = [
    "Artifact",
    "ArtifactKind",
    "Capability",
    "DuplicateProviderError",
    "IdentityArtifact",
    "IncompatibleMediaError",
    "InvalidMediaError",
    "InvalidMetadataError",
    "InvalidNameError",
    "Pipeline",
    "ProcessingCancelledError",
    "Provider",
    "ProviderError",
    "ProviderNotFoundError",
    "ProviderProtocol",
    "Registry",
    "SceneForgeError",
    "register_default_capabilities",
]
