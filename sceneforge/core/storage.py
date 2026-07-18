"""
SceneForge Artifact Store

Nothing in the framework persisted anything before this module
existed. The North Star promise -- "a movie is analyzed once, its
understanding becomes reusable forever" -- is meaningless without a
place for "once" to actually stick.

`content_key()` derives a stable cache key from *what was asked*
(media identity + provider name + provider version), not a random run
id, so re-running the same provider against the same media is a cache
hit rather than a re-run. Upgrading a provider (a real model swap,
e.g. Whisper v2 -> v3) naturally produces a new key instead of
silently serving stale results, because the version is part of the
key.

ArtifactStore is a Protocol so the framework isn't wedded to any one
backend. FileArtifactStore is the smallest useful implementation --
one JSON file per key on disk -- good enough to make caching real
today; swap it for SQLite/Postgres/object storage behind the same
Protocol once real throughput numbers say you need to.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import fields
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.exceptions import ArtifactSerializationError
from sceneforge.media.base import Media

# Registry of Artifact subclasses FileArtifactStore knows how to
# rebuild precisely on read. Anything not registered here still
# round-trips, but comes back as the generic `Artifact` base class
# rather than its original subclass -- register your own Artifact
# subclasses with `register_artifact_type()` to get exact round-trips.
_KNOWN_ARTIFACT_TYPES: dict[str, type[Artifact[Any]]] = {"Artifact": Artifact}


def register_artifact_type(cls: type[Artifact[Any]]) -> type[Artifact[Any]]:
    """
    Class decorator that makes a custom Artifact subclass exactly
    reconstructible by FileArtifactStore (and any store built on
    ``artifact_to_dict``/``artifact_from_dict``).

    Usage:
        @register_artifact_type
        @dataclass(frozen=True, slots=True)
        class TranscriptArtifact(Artifact[str]):
            language: str = "en"
    """
    _KNOWN_ARTIFACT_TYPES[cls.__name__] = cls
    return cls


# Built-in artifact types are pre-registered so out-of-the-box
# round-tripping just works.
from sceneforge.core.identity_artifact import IdentityArtifact  # noqa: E402

register_artifact_type(IdentityArtifact)


def content_key(media: Media, provider_name: str, provider_version: str) -> str:
    """
    Derive a stable, content-addressable cache key.

    Two calls with the same media *identity*, provider name, and
    provider version always produce the same key -- exactly what
    "analyze once, reuse forever" needs: if WhisperProvider v1.2
    already ran on this file, running it again is a lookup, not a
    re-run.
    """
    basis = f"{media.name}:{media.id}:{provider_name}:{provider_version}"
    return sha256(basis.encode("utf-8")).hexdigest()


def _serialize_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, ArtifactKind):
        return value.value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    if isinstance(value, Mapping):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


def artifact_to_dict(artifact: Artifact[Any]) -> dict[str, Any]:
    """Serialize any Artifact (built-in or custom) to a JSON-safe dict."""
    try:
        raw: dict[str, Any] = {
            f.name: getattr(artifact, f.name) for f in fields(artifact)
        }
        raw["__type__"] = type(artifact).__name__
        return {k: _serialize_value(v) for k, v in raw.items()}
    except Exception as exc:  # noqa: BLE001 - re-branded, not swallowed
        raise ArtifactSerializationError(str(exc)) from exc


def artifact_from_dict(data: dict[str, Any]) -> Artifact[Any]:
    """Deserialize a dict produced by ``artifact_to_dict`` back into an Artifact."""
    data = dict(data)
    type_name = data.pop("__type__", "Artifact")
    cls = _KNOWN_ARTIFACT_TYPES.get(type_name, Artifact)

    kwargs: dict[str, Any] = {}
    for f in fields(cls):
        if f.name not in data:
            continue
        value = data[f.name]
        if f.name in ("id", "media_id") and isinstance(value, str):
            value = UUID(value)
        elif f.name == "created_at" and isinstance(value, str):
            value = datetime.fromisoformat(value)
        elif f.name == "kind" and not isinstance(value, ArtifactKind):
            value = ArtifactKind(value)
        elif f.name == "parents":
            value = tuple(UUID(v) if isinstance(v, str) else v for v in value)
        kwargs[f.name] = value

    try:
        return cls(**kwargs)
    except Exception as exc:  # noqa: BLE001 - re-branded, not swallowed
        raise ArtifactSerializationError(str(exc)) from exc


@runtime_checkable
class ArtifactStore(Protocol):
    """Protocol for a content-addressable cache of provider results."""

    def put(self, key: str, artifacts: Iterable[Artifact[Any]]) -> None:
        """Persist artifacts under ``key``, overwriting any existing entry."""
        ...

    def get(self, key: str) -> list[Artifact[Any]] | None:
        """Return cached artifacts for ``key``, or None if there's no entry."""
        ...

    def has(self, key: str) -> bool:
        """Return whether ``key`` has a cached entry."""
        ...

    def delete(self, key: str) -> None:
        """Remove any cached entry for ``key``. No-op if there isn't one."""
        ...


class FileArtifactStore:
    """
    Content-addressable, file-backed ArtifactStore: one JSON file per key.

    Deliberately not a production database. It exists so "a movie is
    analyzed once, its understanding becomes reusable forever" is a
    testable claim today, not just a slogan in a markdown file.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self._root / f"{key}.json"

    def put(self, key: str, artifacts: Iterable[Artifact[Any]]) -> None:
        payload = [artifact_to_dict(a) for a in artifacts]
        self._path(key).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get(self, key: str) -> list[Artifact[Any]] | None:
        path = self._path(key)
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [artifact_from_dict(item) for item in raw]

    def has(self, key: str) -> bool:
        return self._path(key).exists()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()


class InMemoryArtifactStore:
    """
    In-process ArtifactStore backed by a plain dict.

    Useful for tests and for short-lived scripts where disk I/O would
    be pure overhead; the round-trip through ``artifact_to_dict``
    still happens so bugs in serialization show up the same way they
    would with FileArtifactStore.
    """

    def __init__(self) -> None:
        self._data: dict[str, list[dict[str, Any]]] = {}

    def put(self, key: str, artifacts: Iterable[Artifact[Any]]) -> None:
        self._data[key] = [artifact_to_dict(a) for a in artifacts]

    def get(self, key: str) -> list[Artifact[Any]] | None:
        raw = self._data.get(key)
        if raw is None:
            return None
        return [artifact_from_dict(item) for item in raw]

    def has(self, key: str) -> bool:
        return key in self._data

    def delete(self, key: str) -> None:
        self._data.pop(key, None)
