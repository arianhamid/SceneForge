"""
SceneForge Exceptions

Framework-specific exceptions for clear error handling.
"""

from __future__ import annotations


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


class ProviderError(SceneForgeError):
    """Base exception for all provider operations."""


class InvalidMediaError(ProviderError):
    """Raised when media is invalid for processing."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Invalid media: {reason}")


class IncompatibleMediaError(SceneForgeError):
    """Raised when media is incompatible with provider capabilities."""

    def __init__(
        self,
        provider: str,
        media_type: str,
        capabilities: set[str],
    ) -> None:
        self.provider = provider
        self.media_type = media_type
        self.capabilities = capabilities
        super().__init__(
            f"Provider '{provider}' cannot process '{media_type}' "
            f"with capabilities {capabilities}"
        )


class ProviderExecutionError(SceneForgeError):
    """
    Raised by Pipeline when a provider raises during ``run()``.

    Wraps the original exception (available as ``__cause__``) so a
    Pipeline caller always deals with one exception type regardless
    of what a third-party provider throws internally, while never
    hiding the original traceback.
    """

    def __init__(self, provider: str, original: BaseException) -> None:
        self.provider = provider
        self.original = original
        self.__cause__ = original
        super().__init__(f"Provider '{provider}' failed: {original}")


class ProviderTimeoutError(SceneForgeError):
    """Raised when a provider does not complete within its deadline."""

    def __init__(self, provider: str, timeout_seconds: float) -> None:
        self.provider = provider
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Provider '{provider}' timed out after {timeout_seconds}s")


class EnrichmentError(SceneForgeError):
    """Raised when a MediaEnricher fails to enrich a Media object."""

    def __init__(self, enricher: str, original: BaseException) -> None:
        self.enricher = enricher
        self.original = original
        self.__cause__ = original
        super().__init__(f"Enricher '{enricher}' failed: {original}")


class ArtifactStoreError(SceneForgeError):
    """Base exception for artifact persistence failures."""


class ArtifactNotFoundError(ArtifactStoreError):
    """Raised when a lookup key has no cached artifacts."""

    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(f"No cached artifacts for key '{key}'")


class ArtifactSerializationError(ArtifactStoreError):
    """Raised when an artifact payload cannot be serialized/deserialized."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Artifact serialization failed: {reason}")
