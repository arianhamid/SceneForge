"""Tests for MemoryCache."""

from uuid import uuid4

from sceneforge.core.cache import MemoryCache


def test_cache_set_and_get():
    """Cache should store and retrieve items."""
    cache = MemoryCache()
    media_id = uuid4()

    cache.set(media_id, "test_value")

    assert cache.get(media_id) == "test_value"


def test_cache_returns_none_for_missing():
    """Cache should return None for missing items."""
    cache = MemoryCache()
    media_id = uuid4()

    assert cache.get(media_id) is None


def test_cache_invalidate():
    """Cache should invalidate items."""
    cache = MemoryCache()
    media_id = uuid4()

    cache.set(media_id, "test_value")
    assert cache.invalidate(media_id)
    assert cache.get(media_id) is None


def test_cache_max_size():
    """Cache should respect max size."""
    cache = MemoryCache(max_size=2)

    id1 = uuid4()
    id2 = uuid4()
    id3 = uuid4()

    cache.set(id1, "value1")
    cache.set(id2, "value2")
    cache.set(id3, "value3")

    # First item should be evicted
    assert cache.get(id1) is None
    assert cache.get(id2) == "value2"
    assert cache.get(id3) == "value3"
