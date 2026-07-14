"""
SceneForge Local Image Loader

Loads image files from the local filesystem.
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
from .image import ImageMedia

SUPPORTED_EXTENSIONS = frozenset({
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp",
})

_FORMAT_MAP = {
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".png": "PNG",
    ".gif": "GIF",
    ".bmp": "BMP",
    ".tiff": "TIFF",
    ".webp": "WEBP",
}

_MAGIC_BYTES = {
    b"\xff\xd8\xff": "JPEG",
    b"\x89PNG\r\n\x1a\n": "PNG",
    b"GIF87a": "GIF",
    b"GIF89a": "GIF",
    b"BM": "BMP",
    b"II\x2a\x00": "TIFF",
    b"MM\x00\x2a": "TIFF",
    b"RIFF": "WEBP",
}


class LocalImageLoader:
    """
    Loads image files from the local filesystem.

    Returns ImageMedia objects with placeholder dimensions and detected format.
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

        if stat.st_size == 0:
            raise InvalidMediaError(self._path, "File is empty")

        try:
            header = self._path.read_bytes()[:16]
        except OSError as exc:
            raise MediaIOError(self._path, exc) from exc

        fmt = _FORMAT_MAP.get(self._path.suffix.lower(), "UNKNOWN")
        for magic, magic_fmt in _MAGIC_BYTES.items():
            if header.startswith(magic):
                fmt = magic_fmt
                break
        else:
            if fmt != "UNKNOWN":
                raise InvalidMediaError(
                    self._path,
                    f"File does not match expected magic bytes for {fmt}",
                )

        return ImageMedia(
            name=self._path.name,
            width=0,
            height=0,
            fmt=fmt,
            metadata={
                "size_bytes": stat.st_size,
                "modified_at": stat.st_mtime,
                "source": str(self._path),
            },
        )
