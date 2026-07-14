"""
SceneForge Media Exceptions

Framework-specific exception hierarchy for media operations.
"""

from __future__ import annotations

from pathlib import Path


class MediaError(Exception):
    """Base exception for all media operations."""


class MediaNotFoundError(MediaError):
    """Raised when a media file does not exist."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        super().__init__(f"Media not found: {self.path}")


class UnsupportedMediaError(MediaError):
    """Raised when a loader does not support the media type."""

    def __init__(self, extension: str, loader: str) -> None:
        self.extension = extension
        self.loader = loader
        super().__init__(f"'{extension}' is not supported by {loader}")


class InvalidMediaError(MediaError):
    """Raised when media data is corrupted or invalid."""

    def __init__(self, path: str | Path, reason: str) -> None:
        self.path = str(path)
        self.reason = reason
        super().__init__(f"Invalid media '{self.path}': {reason}")


class MediaIOError(MediaError):
    """Raised when an I/O error occurs during media access."""

    def __init__(self, path: str | Path, original: Exception) -> None:
        self.path = str(path)
        self.original = original
        self.__cause__ = original
        super().__init__(f"I/O error accessing '{self.path}': {original}")
