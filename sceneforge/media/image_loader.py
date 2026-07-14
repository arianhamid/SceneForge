"""
SceneForge Local Image Loader

Loads image files from the local filesystem.
"""

from __future__ import annotations

from os import PathLike
from pathlib import Path

from PIL import Image

from .exceptions import (
    InvalidMediaError,
    MediaIOError,
    MediaNotFoundError,
    UnsupportedMediaError,
)
from .image import ImageMedia

SUPPORTED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"})

_FORMAT_MAP = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".gif": "GIF",
    ".bmp": "BMP",
    ".tiff": "TIFF",
    ".webp": "WEBP",
}


class LocalImageLoader:
    """
    Loads image files from the local filesystem.

    Returns ImageMedia objects with decoded dimensions and format.
    """

    def __init__(self, path: str | PathLike[str]) -> None:
        self._path = Path(path)

    def load(self) -> ImageMedia:
        """Load and return an ImageMedia object."""
        if not self._path.exists():
            raise MediaNotFoundError(self._path)

        if self._path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise UnsupportedMediaError(self._path.suffix, "LocalImageLoader")

        try:
            stat = self._path.stat()
        except OSError as exc:
            raise MediaIOError(self._path, exc) from exc

        try:
            with Image.open(self._path) as img:
                width, height = img.size
                fmt = img.format or _FORMAT_MAP.get(self._path.suffix.lower(), "UNKNOWN")
        except Exception as exc:
            raise InvalidMediaError(self._path, str(exc)) from exc

        return ImageMedia(
            name=self._path.name,
            width=width,
            height=height,
            fmt=fmt,
            metadata={
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
                "source": str(self._path),
            },
        )
