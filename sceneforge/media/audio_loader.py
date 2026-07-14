"""
SceneForge Local Audio Loader

Loads audio files from the local filesystem.
"""

from __future__ import annotations

from os import PathLike
from pathlib import Path

from .audio import AudioMedia
from .exceptions import (
    InvalidMediaError,
    MediaIOError,
    MediaNotFoundError,
    UnsupportedMediaError,
)

SUPPORTED_EXTENSIONS = frozenset(
    {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac", ".wma"}
)


class LocalAudioLoader:
    """
    Loads audio files from the local filesystem.

    Returns AudioMedia objects without decoding audio data.
    """

    def __init__(self, path: str | PathLike[str]) -> None:
        self._path = Path(path)

    def load(self) -> AudioMedia:
        """Load and return an AudioMedia object."""
        if not self._path.exists():
            raise MediaNotFoundError(self._path)

        if self._path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise UnsupportedMediaError(self._path.suffix, "LocalAudioLoader")

        try:
            stat = self._path.stat()
        except OSError as exc:
            raise MediaIOError(self._path, exc) from exc

        if stat.st_size == 0:
            raise InvalidMediaError(self._path, "File is empty")

        return AudioMedia(
            name=self._path.name,
            duration=0.0,  # Placeholder - will be decoded by providers
            sample_rate=0,  # Placeholder - will be decoded by providers
            channels=0,  # Placeholder - will be decoded by providers
            metadata={
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
                "source": str(self._path),
            },
        )
