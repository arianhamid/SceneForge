"""
SceneForge Provider Registry Example

Demonstrates registering and discovering providers.
"""

from sceneforge.contrib.identity import IdentityProvider
from sceneforge.core.registry import Registry

# Create registry
registry = Registry()

# Register providers
registry.register(IdentityProvider())

# Discover providers
for provider in registry.providers():
    print(f"Provider: {provider.name}, Version: {provider.version}")
