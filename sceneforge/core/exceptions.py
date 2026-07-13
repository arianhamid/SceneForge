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


class ProcessingCancelledError(SceneForgeError):
    """Pipeline execution was cancelled."""

    def __init__(self) -> None:
        super().__init__("Processing was cancelled.")


class InvalidNameError(SceneForgeError):
    """Raised when a provider name does not conform to naming rules."""

    def __init__(self, name: str) -> None:
        super().__init__(f"Invalid qualified name: {name!r}")
        self.name = name


class InvalidMetadataError(SceneForgeError):
    """Raised when provider metadata contains invalid fields."""

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(f"Invalid metadata field '{field}': {reason}")
        self.field = field
        self.reason = reason
