"""
SceneForge Entity Store

Resolves the Sprint 4 open question ("does ArtifactStore extend to
Entity, or does Entity need its own shape?") with a real spike rather
than a design doc, per `.ai/NEXT_TASK.md`.

The answer: **a separate `EntityStore`, not a shared generic with
`ArtifactStore`.** The JSON-serialization mechanics turned out to be
close to identical -- `Entity` and `Artifact` are both flat, frozen
dataclasses with a UUID id, a kind enum, a `MappingProxyType`
metadata field, and a `parents` tuple -- so this file mirrors
`sceneforge/core/storage.py` closely. But the field names genuinely
differ (`Entity.builder` vs `Artifact.provider`, `EntityKind` vs
`ArtifactKind`), and the cache-key *basis* differs in a way that
matters: an Artifact's cache key is "media identity + provider" (one
provider, one media object); an Entity's natural cache key is "the
exact set of input artifact ids + builder" (a builder synthesizes
across many artifacts, possibly many media objects at once -- see
`SceneGroupingBuilder.build()`, which groups a whole mixed batch by
`media_id` internally). Forcing both through one generic `Store[T]`
would have meant bending one of those two key shapes to fit the other.
See `docs/adr/0012-entity-persistence.md` for the full writeup.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, fields
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

from sceneforge.core.artifact import Artifact
from sceneforge.core.exceptions import ArtifactSerializationError
from sceneforge.knowledge.entity import Entity, EntityKind, Provenance

_KNOWN_ENTITY_TYPES: dict[str, type[Entity[Any]]] = {"Entity": Entity}


def register_entity_type(cls: type[Entity[Any]]) -> type[Entity[Any]]:
    """Class decorator making a custom Entity subclass exactly reconstructible."""
    _KNOWN_ENTITY_TYPES[cls.__name__] = cls
    return cls


def entity_build_key(
    artifacts: Iterable[Artifact[Any]], builder_name: str, builder_version: str
) -> str:
    """
    Derive a stable cache key for a KnowledgeBuilder run.

    Keyed on the exact *set* of input artifact ids plus builder
    identity, not on a single media object -- a builder can (and
    `SceneGroupingBuilder` does) synthesize entities from a batch
    spanning several media objects at once. Two calls with the same
    artifact set and the same builder version are the same question
    asked twice; two calls where even one artifact differs (a new
    scene got detected, a transcript was re-run) are a different
    question and must not collide.
    """
    ids = sorted(str(a.id) for a in artifacts)
    basis = f"{builder_name}:{builder_version}:{','.join(ids)}"
    return sha256(basis.encode("utf-8")).hexdigest()


def _serialize_value(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, EntityKind):
        return value.value
    if isinstance(value, Provenance):
        return {
            "builder": value.builder,
            "source_artifact_ids": _serialize_value(value.source_artifact_ids),
            "confidence": value.confidence,
        }
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    if isinstance(value, Mapping):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


def entity_to_dict(entity: Entity[Any]) -> dict[str, Any]:
    """Serialize any Entity (built-in or custom) to a JSON-safe dict."""
    try:
        raw: dict[str, Any] = {f.name: getattr(entity, f.name) for f in fields(entity)}
        raw["__type__"] = type(entity).__name__
        return {k: _serialize_value(v) for k, v in raw.items()}
    except Exception as exc:  # noqa: BLE001 - re-branded, not swallowed
        raise ArtifactSerializationError(str(exc)) from exc


def _deserialize_provenance(value: Any) -> Provenance | None:
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise TypeError("provenance must be a mapping or null")

    builder = value["builder"]
    if not isinstance(builder, str):
        raise TypeError("provenance.builder must be a string")

    raw_source_ids = value.get("source_artifact_ids", ())
    if not isinstance(raw_source_ids, (list, tuple)):
        raise TypeError("provenance.source_artifact_ids must be a sequence")

    source_artifact_ids: list[UUID] = []
    for source_id in raw_source_ids:
        if isinstance(source_id, UUID):
            source_artifact_ids.append(source_id)
        elif isinstance(source_id, str):
            source_artifact_ids.append(UUID(source_id))
        else:
            raise TypeError("provenance source artifact ids must be UUIDs or strings")

    confidence = value.get("confidence")
    if confidence is not None:
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise TypeError("provenance.confidence must be a number or null")
        confidence = float(confidence)

    return Provenance(
        builder=builder,
        source_artifact_ids=tuple(source_artifact_ids),
        confidence=confidence,
    )


def entity_from_dict(data: dict[str, Any]) -> Entity[Any]:
    """Deserialize a dict produced by `entity_to_dict` back into an Entity."""
    try:
        data = dict(data)
        type_name = data.pop("__type__", "Entity")
        if not isinstance(type_name, str):
            raise TypeError("__type__ must be a string")
        cls = _KNOWN_ENTITY_TYPES.get(type_name, Entity)

        kwargs: dict[str, Any] = {}
        for f in fields(cls):
            if f.name not in data:
                continue
            value = data[f.name]
            if f.name == "id" and isinstance(value, str):
                value = UUID(value)
            elif f.name == "created_at" and isinstance(value, str):
                value = datetime.fromisoformat(value)
            elif f.name == "kind" and not isinstance(value, EntityKind):
                value = EntityKind(value)
            elif f.name == "parents":
                value = tuple(UUID(v) if isinstance(v, str) else v for v in value)
            elif f.name == "provenance":
                value = _deserialize_provenance(value)
            kwargs[f.name] = value

        return cls(**kwargs)
    except Exception as exc:  # noqa: BLE001 - re-branded, not swallowed
        raise ArtifactSerializationError(str(exc)) from exc


@runtime_checkable
class EntityStore(Protocol):
    """Protocol for a cache of Knowledge Builder output.

    Keyed by `entity_build_key()`.
    """

    def put(self, key: str, entities: Iterable[Entity[Any]]) -> None: ...

    def get(self, key: str) -> list[Entity[Any]] | None: ...

    def has(self, key: str) -> bool: ...

    def delete(self, key: str) -> None: ...

    def keys(self) -> list[str]:
        """
        Return every key currently stored.

        Added in Sprint 7 (`docs/adr/0014-relationship-query-spike.md`)
        specifically to make querying possible at all: without this,
        an `EntityStore` can only answer "what did I already ask for
        by this exact key" -- it cannot answer "what's in here." A
        query like "every scene entity X relates to" needs to iterate
        everything before it can filter, and iteration needs
        enumeration.
        """
        ...


class FileEntityStore:
    """Content-addressable, file-backed EntityStore: one JSON file per key."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self._root / f"{key}.json"

    def put(self, key: str, entities: Iterable[Entity[Any]]) -> None:
        payload = [entity_to_dict(e) for e in entities]
        self._path(key).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def get(self, key: str) -> list[Entity[Any]] | None:
        path = self._path(key)
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        return [entity_from_dict(item) for item in raw]

    def has(self, key: str) -> bool:
        return self._path(key).exists()

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    def keys(self) -> list[str]:
        return [path.stem for path in self._root.glob("*.json")]


class InMemoryEntityStore:
    """In-process EntityStore backed by a plain dict. For tests and short scripts."""

    def __init__(self) -> None:
        self._data: dict[str, list[dict[str, Any]]] = {}

    def put(self, key: str, entities: Iterable[Entity[Any]]) -> None:
        self._data[key] = [entity_to_dict(e) for e in entities]

    def get(self, key: str) -> list[Entity[Any]] | None:
        raw = self._data.get(key)
        if raw is None:
            return None
        return [entity_from_dict(item) for item in raw]

    def has(self, key: str) -> bool:
        return key in self._data

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def keys(self) -> list[str]:
        return list(self._data.keys())


def iter_all_entities(store: EntityStore) -> Iterable[Entity[Any]]:
    """
    Load and yield every Entity currently in `store`.

    The naive query primitive: enumerate every key, fetch it, flatten
    the results. This is what "querying" an EntityStore actually means
    today -- there is no index, no filtering pushed down to storage.
    Whether that's good enough is exactly Sprint 7's question; see
    `docs/adr/0014-relationship-query-spike.md` for the answer found by
    measuring this against a realistic synthetic dataset rather than
    assuming.
    """
    for key in store.keys():  # noqa: SIM118 - EntityStore.keys(), not dict.keys()
        entities = store.get(key)
        if entities:
            yield from entities


def find_related(store: EntityStore, entity_id: UUID) -> list[Entity[Any]]:
    """
    Return every Entity whose `parents` include `entity_id`.

    The concrete query this spike exists to answer: "what relates to
    this entity?" Built directly on `iter_all_entities` -- no index,
    full scan every call. See `docs/adr/0014-relationship-query-spike.md`
    for whether that's fast enough in practice and where it would stop
    being so.
    """
    return [e for e in iter_all_entities(store) if entity_id in e.parents]


@dataclass(frozen=True, slots=True)
class KnowledgeRecord:
    """
    One durable, revisioned version of a Knowledge Builder's conclusion
    for `key` (ADR-0024 Phase 0 item 4).

    Distinct from an `EntityStore` cache entry: a `KnowledgeRecordStore`
    never overwrites or deletes what it already knows. Correcting a
    conclusion means calling `append()` again, which always creates
    revision N+1 -- revision N's bytes remain readable through
    `history()`. `retracted` marks a revision as withdrawn without
    erasing it, so "we no longer believe this" is itself a durable,
    dated fact rather than a silent disappearance. This is exactly what
    a cache doesn't give you: evicting a stale `FileEntityStore` entry
    and correcting an earlier conclusion look identical there, which is
    the gap this ADR item exists to close.
    """

    key: str
    revision: int
    entities: tuple[Entity[Any], ...]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    retracted: bool = False
    retracted_reason: str | None = None


def _record_to_dict(record: KnowledgeRecord) -> dict[str, Any]:
    return {
        "key": record.key,
        "revision": record.revision,
        "entities": [entity_to_dict(e) for e in record.entities],
        "created_at": record.created_at.isoformat(),
        "retracted": record.retracted,
        "retracted_reason": record.retracted_reason,
    }


def _record_from_dict(data: dict[str, Any]) -> KnowledgeRecord:
    try:
        return KnowledgeRecord(
            key=data["key"],
            revision=data["revision"],
            entities=tuple(entity_from_dict(e) for e in data["entities"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            retracted=data["retracted"],
            retracted_reason=data.get("retracted_reason"),
        )
    except Exception as exc:  # noqa: BLE001 - re-branded, not swallowed
        raise ArtifactSerializationError(str(exc)) from exc


@runtime_checkable
class KnowledgeRecordStore(Protocol):
    """
    Protocol for the durable, append-only counterpart to `EntityStore`.

    Where `EntityStore` answers "what did this exact computation
    already produce" (evictable, overwritable, keyed by input-artifact
    set + builder), `KnowledgeRecordStore` answers "what has this
    project ever concluded about `key`, and does it still believe it."
    There is no `put`/`delete` here on purpose -- only `append` and
    `retract`, because durability is the entire point.
    """

    def append(
        self,
        key: str,
        entities: Iterable[Entity[Any]],
        *,
        retracted: bool = False,
        retracted_reason: str | None = None,
    ) -> KnowledgeRecord:
        """Persist a new revision for `key`. Never overwrites a prior one."""
        ...

    def latest(self, key: str) -> KnowledgeRecord | None:
        """Return the most recent revision for `key`, or None if there is none.

        "Most recent" includes retracted revisions -- a retraction is
        itself the latest fact about `key` until superseded again.
        Callers that specifically want the last non-retracted answer
        should read `history()` and filter."""
        ...

    def history(self, key: str) -> list[KnowledgeRecord]:
        """Return every revision ever recorded for `key`, oldest first."""
        ...

    def retract(self, key: str, reason: str) -> KnowledgeRecord:
        """Append a new, empty, `retracted=True` revision for `key`."""
        ...

    def keys(self) -> list[str]:
        """Return every key that has at least one revision."""
        ...


class FileKnowledgeRecordStore:
    """
    Durable, file-backed `KnowledgeRecordStore`.

    Layout: one directory per key under `root`, one JSON file per
    revision inside it (`0001.json`, `0002.json`, ...). This class
    never overwrites or deletes a revision file -- `append()` always
    creates a new one; `latest()`/`history()` only ever read what's
    already on disk. Initially the same file format as
    `FileEntityStore`, deliberately: ADR-0024 item 4 asks for the cache
    and evidence *roles* to be distinct, not necessarily a different
    storage technology on day one.
    """

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _key_dir(self, key: str) -> Path:
        return self._root / key

    def append(
        self,
        key: str,
        entities: Iterable[Entity[Any]],
        *,
        retracted: bool = False,
        retracted_reason: str | None = None,
    ) -> KnowledgeRecord:
        key_dir = self._key_dir(key)
        key_dir.mkdir(parents=True, exist_ok=True)
        next_revision = len(list(key_dir.glob("*.json"))) + 1
        record = KnowledgeRecord(
            key=key,
            revision=next_revision,
            entities=tuple(entities),
            retracted=retracted,
            retracted_reason=retracted_reason,
        )
        path = key_dir / f"{next_revision:04d}.json"
        path.write_text(json.dumps(_record_to_dict(record), indent=2), encoding="utf-8")
        return record

    def latest(self, key: str) -> KnowledgeRecord | None:
        history = self.history(key)
        return history[-1] if history else None

    def history(self, key: str) -> list[KnowledgeRecord]:
        key_dir = self._key_dir(key)
        if not key_dir.is_dir():
            return []
        paths = sorted(key_dir.glob("*.json"))
        return [
            _record_from_dict(json.loads(p.read_text(encoding="utf-8"))) for p in paths
        ]

    def retract(self, key: str, reason: str) -> KnowledgeRecord:
        return self.append(key, entities=(), retracted=True, retracted_reason=reason)

    def keys(self) -> list[str]:
        return [p.name for p in self._root.iterdir() if p.is_dir()]


class InMemoryKnowledgeRecordStore:
    """In-process `KnowledgeRecordStore` backed by a plain dict. For tests."""

    def __init__(self) -> None:
        self._data: dict[str, list[KnowledgeRecord]] = {}

    def append(
        self,
        key: str,
        entities: Iterable[Entity[Any]],
        *,
        retracted: bool = False,
        retracted_reason: str | None = None,
    ) -> KnowledgeRecord:
        history = self._data.setdefault(key, [])
        record = KnowledgeRecord(
            key=key,
            revision=len(history) + 1,
            entities=tuple(entities),
            retracted=retracted,
            retracted_reason=retracted_reason,
        )
        history.append(record)
        return record

    def latest(self, key: str) -> KnowledgeRecord | None:
        history = self._data.get(key)
        return history[-1] if history else None

    def history(self, key: str) -> list[KnowledgeRecord]:
        return list(self._data.get(key, []))

    def retract(self, key: str, reason: str) -> KnowledgeRecord:
        return self.append(key, entities=(), retracted=True, retracted_reason=reason)

    def keys(self) -> list[str]:
        return list(self._data.keys())
