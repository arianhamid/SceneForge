"""
SceneForge Local Video Loader

Loads video files from the local filesystem.
"""

from __future__ import annotations

from os import PathLike
from pathlib import Path

from .exceptions import (
    InvalidMediaError,
    MediaIOError,
    MediaNotFoundError,
    UnsupportedMediaError,
)
from .video import VideoMedia

SUPPORTED_EXTENSIONS = frozenset(
    {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"}
)


class LocalVideoLoader:
    """
    Loads video files from the local filesystem.

    Returns VideoMedia objects without decoding video data.
    """

    def __init__(self, path: str | PathLike[str]) -> None:
        self._path = Path(path)

    def load(self) -> VideoMedia:
        """Load and return a VideoMedia object."""
        if not self._path.exists():
            raise MediaNotFoundError(self._path)

        if self._path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise UnsupportedMediaError(self._path.suffix, "LocalVideoLoader")

        try:
            stat = self._path.stat()
        except OSError as exc:
            raise MediaIOError(self._path, exc) from exc

        if stat.st_size == 0:
            raise InvalidMediaError(self._path, "File is empty")

        return VideoMedia(
            name=self._path.name,
            duration=0.0,  # Placeholder - will be decoded by providers
            codec="unknown",  # Placeholder - will be decoded by providers
            fps=0.0,  # Placeholder - will be decoded by providers
            metadata={
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
                "source": str(self._path),
            },
        )
