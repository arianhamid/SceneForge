"""
MediaHash Provider.

Computes content hashes for media files. Useful for:
- Deduplication
- Cache invalidation
- Content integrity verification
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from sceneforge.contrib.media_hash.artifact import MediaHashArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.provider import Provider
from sceneforge.media.base import Media


class MediaHashProvider(Provider):
    """
    Provider that computes deterministic content hashes for media.

    Uses SHA-256 for hashing. When a source path is available in
    metadata, hashes the actual file content. Otherwise falls back
    to a name-based identity hash.
    """

    @property
    def name(self) -> str:
        return "media_hash"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset()

    def run(self, media: Media) -> list[Artifact[Any]]:
        """Process media and return content hash artifact."""
        source_path = media.metadata.get("source")

        if source_path and Path(source_path).is_file():
            hash_value = self._hash_file(source_path)
            source_type = "file"
        else:
            hash_value = self._hash_identity(media.name)
            source_type = "identity"

        return [
            MediaHashArtifact(
                media_id=media.id,
                hash_value=hash_value,
                algorithm="sha256",
                source_type=source_type,
                provider=self.name,
            )
        ]

    def _hash_file(self, path: str) -> str:
        """Compute SHA-256 hash of file contents."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _hash_identity(self, name: str) -> str:
        """Compute deterministic hash from media name."""
        return hashlib.sha256(name.encode("utf-8")).hexdigest()
