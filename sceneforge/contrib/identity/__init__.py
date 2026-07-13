"""
SceneForge Identity Provider.

The simplest possible provider - returns artifacts unchanged.
Validates the architecture without external dependencies.
"""

from sceneforge.contrib.identity.provider import IdentityProvider

__all__ = ["IdentityProvider"]
