"""
SceneForge Cache

Simple in-memory cache for decoded representations.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID


class MemoryCache:
    """
    Simple in-memory cache.

    Stores decoded representations by media ID.
    """

    def __init__(self, max_size: int = 100) -> None:
        """
        Initialize MemoryCache.

        Args:
            max_size: Maximum number of items to cache.
        """
        self._cache: dict[UUID, Any] = {}
        self._max_size = max_size

    def get(self, media_id: UUID) -> Any | None:
        """
        Get cached item by media ID.

        Args:
            media_id: The media ID to look up.

        Returns:
            Cached item or None if not found.
        """
        return self._cache.get(media_id)

    def set(self, media_id: UUID, value: Any) -> None:
        """
        Store item in cache.

        Args:
            media_id: The media ID to store under.
            value: The value to cache.
        """
        if len(self._cache) >= self._max_size:
            # Remove oldest item (simplified: remove first key)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[media_id] = value

    def invalidate(self, media_id: UUID) -> bool:
        """
        Remove item from cache.

        Args:
            media_id: The media ID to remove.

        Returns:
            True if item was removed, False if not found.
        """
        if media_id in self._cache:
            del self._cache[media_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()

    def __len__(self) -> int:
        """Return number of cached items."""
        return len(self._cache)
