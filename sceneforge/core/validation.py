"""
SceneForge Validation Utilities.

Functions for validating framework objects.
"""

from __future__ import annotations

from sceneforge.core.provider_metadata import ProviderMetadata


def validate_provider_metadata(metadata: ProviderMetadata) -> None:
    """Validate provider metadata fields."""

    if not metadata.name:
        raise ValueError("Provider name cannot be empty.")

    if not metadata.version:
        raise ValueError("Provider version cannot be empty.")
