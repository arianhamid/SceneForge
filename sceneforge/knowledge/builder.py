"""
SceneForge Knowledge Builder Protocol

A Knowledge Builder turns Artifacts (single-provider observations)
into Entities (a synthesis across possibly many artifacts, possibly
from several providers) -- see docs/architecture/DOMAIN_MODEL.md's
"Entity" section and docs/architecture/LAYERS.md's Layer 4.

Knowledge Builders:
  * read Artifacts, never modify them
  * may read across multiple providers' output for the same media
  * must not call Providers or Applications directly
  * produce Entities, which are themselves immutable
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from sceneforge.core.artifact import Artifact
from sceneforge.knowledge.entity import Entity


@runtime_checkable
class KnowledgeBuilder(Protocol):
    """Structural contract for turning Artifacts into Entities."""

    @property
    def name(self) -> str:
        """Return the builder name."""
        ...

    @property
    def version(self) -> str:
        """Return the builder version."""
        ...

    def build(self, artifacts: list[Artifact[Any]]) -> list[Entity[Any]]:
        """Synthesize Entities from a collection of Artifacts."""
        ...


def build_with_cache(
    builder: KnowledgeBuilder,
    artifacts: list[Artifact[Any]],
    store: Any | None = None,
) -> list[Entity[Any]]:
    """
    Run a KnowledgeBuilder, checking/populating an EntityStore first.

    Deliberately a function, not a `KnowledgeBuilderPipeline` class --
    `Pipeline` exists because Providers needed retries, timeouts,
    cancellation, and enrichment around a single call; nothing about
    Knowledge Builders has demonstrated a need for that machinery yet
    (a builder is a pure, fast, synchronous transform over data
    already in memory). Building that class before a second real
    Knowledge Builder exists to prove the need would repeat the exact
    premature-abstraction mistake `docs/adr/0011-first-knowledge-builder-scope.md`
    was written to avoid. If that need materializes, promote this
    function into a class then -- not before.

    `store` is typed as `Any` here (rather than importing
    `sceneforge.knowledge.storage.EntityStore`) to avoid this module
    depending on the storage module; any object satisfying
    `EntityStore`'s `get`/`put` shape works.
    """
    if store is None:
        return builder.build(artifacts)

    from sceneforge.knowledge.storage import entity_build_key

    key = entity_build_key(artifacts, builder.name, builder.version)
    cached: list[Entity[Any]] | None = store.get(key)
    if cached is not None:
        return cached

    entities = builder.build(artifacts)
    store.put(key, entities)
    return entities
