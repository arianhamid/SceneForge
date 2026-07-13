"""
SceneForge Exceptions

Framework-specific exceptions for clear error handling.
"""


class SceneForgeError(Exception):
    """Base exception for all SceneForge errors."""


class DuplicateProviderError(SceneForgeError):
    """Raised when registering a provider with a name that already exists."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Provider '{name}' already registered.")
        self.name = name


class ProviderNotFoundError(SceneForgeError):
    """Raised when a provider is not found in the registry."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Provider '{name}' not found.")
        self.name = name
