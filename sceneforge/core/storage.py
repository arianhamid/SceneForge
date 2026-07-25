"""
SceneForge Artifact Store

Nothing in the framework persisted anything before this module
existed. The North Star promise -- "a movie is analyzed once, its
understanding becomes reusable forever" -- is meaningless without a
place for "once" to actually stick.

`content_key()` derives a stable cache key from *what was asked*
(media content identity + provider name + provider version + execution
fingerprint), not a random run id or the random per-load `Media.id`, so
re-running the same provider with the same configuration against the
same file content is a cache hit rather than a re-run. Upgrading a
provider (a real model swap, e.g. Whisper v2 -> v3) naturally produces
a new key instead of silently serving stale results, because the
version is part of the key -- and so does reconfiguring a provider's
execution parameters, via `execution_fingerprint` (ADR-0024 Phase 0
item 2).

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


def media_content_identity(media: Media) -> str:
    """
    Derive a stable content identity for `media`, independent of the
    random per-load `media.id`.

    Two loads of the same unchanged file must resolve to the same
    identity, and two different files must not collide. When a real
    file backs the media (`metadata["source"]` set by a `Local*Loader`
    and still present on disk), hash its actual bytes. Otherwise --
    synthetic or in-memory media with no backing file, common in tests
    -- fall back to a deterministic hash of `media.name`. This mirrors
    `MediaHashProvider`'s existing two-tier strategy
    (`sceneforge/contrib/media_hash/provider.py`) rather than importing
    it: Core cannot depend on `contrib`
    (`tests/architecture/test_import_rules.py`), and that provider
    exists to produce a separate, durable, queryable hash Artifact, not
    a cache-key primitive.

    The name-based fallback is a known, weaker identity notion --
    documented, not hidden: two unrelated synthetic `Media` objects
    that happen to share a name will collide under it. Real files
    (the case that matters for the "analyze once, reuse forever"
    promise) always get a true content hash.
    """
    source = media.metadata.get("source")
    if source and Path(str(source)).is_file():
        digest = sha256()
        with open(source, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    return sha256(media.name.encode("utf-8")).hexdigest()


def content_key(
    media: Media,
    provider_name: str,
    provider_version: str,
    execution_fingerprint: str = "",
) -> str:
    """
    Derive a stable, content-addressable cache key.

    Two calls with the same media *content*, provider name, provider
    version, and execution fingerprint always produce the same key --
    exactly what "analyze once, reuse forever" needs: if WhisperProvider
    v1.2 already ran on this file with this configuration, running it
    again is a lookup, not a re-run.

    Basis is content identity (real file-bytes hash, or a documented
    name-based fallback for media with no backing file -- see
    `media_content_identity()`), not the random `Media.id` assigned per
    load: reloading the same unchanged file must be a cache hit, not a
    guaranteed miss. `execution_fingerprint` folds in whatever
    provider configuration (model revision, prompt/template version,
    sampling parameters, ...) actually changes the provider's output,
    so two differently configured instances of the same
    name/version do not collide (ADR-0024 Phase 0 item 2; before this,
    `content_key()` had no way to distinguish them).
    """
    basis = (
        f"{media_content_identity(media)}:{provider_name}:{provider_version}"
        f":{execution_fingerprint}"
    )
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

    def keys(self) -> list[str]:
        """
        Return every key currently stored.

        Added for ADR-0024 Phase 0 item 3: artifact lookup by ID and by
        media needs to enumerate before it can filter, the same reason
        `EntityStore.keys()` was added in ADR-0014. This was previously
        the one asymmetry between `ArtifactStore` and `EntityStore`
        (tracked in `PROJECT_STATE.md`'s Known Problems as "no real
        artifact-query caller has required it yet") -- the evidence
        lookup below is that caller.
        """
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

    def keys(self) -> list[str]:
        return [path.stem for path in self._root.glob("*.json")]


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

    def keys(self) -> list[str]:
        return list(self._data.keys())


def iter_all_artifacts(store: ArtifactStore) -> Iterable[Artifact[Any]]:
    """
    Load and yield every Artifact currently in `store`.

    The naive query primitive, matching `iter_all_entities()` in
    `knowledge/storage.py` exactly: enumerate every key, fetch it,
    flatten. No index, no filtering pushed down to storage -- fine at
    the measured scale precedent set by ADR-0014/ADR-0019 for
    `EntityStore`; revisit only if a real query demonstrates this
    doesn't hold for `ArtifactStore` too.
    """
    for key in store.keys():  # noqa: SIM118 - ArtifactStore.keys(), not dict.keys()
        artifacts = store.get(key)
        if artifacts:
            yield from artifacts


def find_artifact_by_id(
    store: ArtifactStore, artifact_id: UUID
) -> Artifact[Any] | None:
    """
    Return the Artifact with `artifact_id`, or None if no cached entry has it.

    The concrete gap ADR-0024 Phase 0 item 3 exists to close: before
    this, nothing let an application resolve an `EvidenceLink`'s
    `Reference(kind=ReferenceKind.ARTIFACT, id=...)` back to the actual
    Artifact it points at.
    """
    for artifact in iter_all_artifacts(store):
        if artifact.id == artifact_id:
            return artifact
    return None


def find_artifacts_by_media(
    store: ArtifactStore, media_id: UUID
) -> list[Artifact[Any]]:
    """
    Return every Artifact produced from `media_id`.

    Artifact's base class carries no `media_id` field -- concrete
    subclasses add it (see `SceneCutArtifact`, `TranscriptSegmentArtifact`,
    etc.), so this reads it structurally via `getattr` rather than
    assuming every Artifact has one. An Artifact with no `media_id`
    attribute at all is simply excluded, not an error.
    """
    return [
        a for a in iter_all_artifacts(store) if getattr(a, "media_id", None) == media_id
    ]
