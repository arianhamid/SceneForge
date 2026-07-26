"""
SceneForge Scene Summary Application

A simple, first-pass application that demonstrates the framework's
application layer pattern. Reads scene entities from an EntityStore,
collects structured data, and renders a human-readable Markdown summary.

This is intentionally minimal -- it exists to prove the framework's
success definition: that applications can be built on top of the
knowledge layer without modifying any core components.

Also renders `Fact`-kind Entities (real since `FactExtractionBuilder`,
`sceneforge/knowledge/fact_extraction_builder.py`). Facts are now
correlated to the Scene they belong to where possible: a Fact's own
`media_id` is whatever image it was captioned from (typically an
extracted frame), which is not the same media a `SceneCutArtifact`'s
`media_id` refers to (the source video), so `media_id` cannot be the
join key -- the same reason `SceneFaceBuilder`/`SceneTextBuilder`
never used it either (ADR-0016). Instead this reuses that exact
established mechanism: a Fact's `metadata["source_frame_path"]`
(real since `FactExtractionBuilder`, populated by
`TransformersCaptionProvider`/`TransformersObjectDetectionProvider`)
is matched against the `frame_paths` list already present on
`SceneGroupingBuilder`'s `SCENE` entities. No new builder, Protocol,
or persisted type was added for this -- it is read-time correlation
over data both sides already carry, done here rather than in a new
Knowledge/Relationship Builder because nothing needs the correlation
to be a durable, queryable Entity yet (see the former Future Ideas
entry this closes in `PROJECT_STATE.md`). A Fact whose
`source_frame_path` doesn't match any known scene's frames (no frame
extraction ran, or the Fact came from a standalone image) is left in
the flat "Facts" section instead of being silently dropped.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.storage import EntityStore, iter_all_entities


@dataclass(frozen=True, slots=True)
class SceneData:
    """Structured data for a single scene."""

    scene_index: int
    start_seconds: float
    end_seconds: float
    frame_count: int
    transcript_segment_count: int
    dialogue: str | None
    facts: tuple[FactData, ...] = ()


@dataclass(frozen=True, slots=True)
class FactData:
    """Structured data for a single Fact."""

    statement: str
    media_id: str
    source_provider: str | None
    prompt: str | None
    scene_index: int | None = None


@dataclass(frozen=True, slots=True)
class SceneSummaryData:
    """Structured summary of all scenes and facts."""

    scenes: tuple[SceneData, ...] = ()
    facts: tuple[FactData, ...] = ()


class SceneSummary:
    """
    Collects scene entities from an EntityStore and renders a Markdown summary.

    Usage:
        store = InMemoryEntityStore()
        # ... populate store with scene entities ...
        summary = SceneSummary(store)
        data = summary.collect()
        markdown = summary.render_markdown()
        # or
        data, markdown = summary.generate()
    """

    def __init__(self, store: EntityStore) -> None:
        self._store = store

    def collect(self) -> SceneSummaryData:
        """
        Collect all scene and fact entities from the store and return
        structured data.

        Scenes: reads metadata keys scene_index, start_seconds,
        end_seconds, frame_paths, transcript_segment_count. Uses
        entity.payload for dialogue text.

        Facts: reads entity.payload for the statement text, and
        metadata keys media_id, source_provider, prompt,
        source_frame_path.

        A Fact is correlated to a scene when its
        `source_frame_path` matches a path in some scene's
        `frame_paths` -- the same mechanism `SceneFaceBuilder`/
        `SceneTextBuilder` use (ADR-0016), applied here at read time.
        Correlated facts appear under their scene's `SceneData.facts`
        and are excluded from the top-level flat `facts` list;
        uncorrelated facts (no match, or no `source_frame_path` at
        all) remain in the flat list, same as before this method
        knew how to correlate anything.
        """
        scene_entities: list[Entity[Any]] = []
        fact_entities: list[Entity[Any]] = []
        frame_path_to_scene_id: dict[str, UUID] = {}
        scene_index_by_id: dict[UUID, int] = {}

        for entity in iter_all_entities(self._store):
            if entity.kind == EntityKind.SCENE:
                scene_entities.append(entity)
                meta = entity.metadata
                scene_index = meta.get("scene_index", 0)
                scene_index_by_id[entity.id] = scene_index
                for frame_path in meta.get("frame_paths", []):
                    frame_path_to_scene_id[frame_path] = entity.id
            elif entity.kind == EntityKind.FACT:
                if entity.payload:
                    fact_entities.append(entity)

        facts_by_scene_id: dict[UUID, list[FactData]] = defaultdict(list)
        uncorrelated_facts: list[FactData] = []
        for entity in fact_entities:
            meta = entity.metadata
            source_frame_path = meta.get("source_frame_path")
            scene_id = (
                frame_path_to_scene_id.get(source_frame_path)
                if source_frame_path
                else None
            )
            scene_index = scene_index_by_id[scene_id] if scene_id is not None else None
            fact_data = FactData(
                statement=entity.payload,
                media_id=meta.get("media_id", ""),
                source_provider=meta.get("source_provider"),
                prompt=meta.get("prompt"),
                scene_index=scene_index,
            )
            if scene_id is None:
                uncorrelated_facts.append(fact_data)
            else:
                facts_by_scene_id[scene_id].append(fact_data)

        scenes = []
        for scene_entity in scene_entities:
            meta = scene_entity.metadata
            scene_index = meta.get("scene_index", 0)
            scenes.append(
                SceneData(
                    scene_index=scene_index,
                    start_seconds=meta.get("start_seconds", 0.0),
                    end_seconds=meta.get("end_seconds", 0.0),
                    frame_count=len(meta.get("frame_paths", [])),
                    transcript_segment_count=meta.get("transcript_segment_count", 0),
                    dialogue=scene_entity.payload,
                    facts=tuple(facts_by_scene_id.get(scene_entity.id, [])),
                )
            )
        scenes.sort(key=lambda s: s.scene_index)
        return SceneSummaryData(scenes=tuple(scenes), facts=tuple(uncorrelated_facts))

    def render_markdown(self) -> str:
        """
        Render a Markdown summary of all scenes and facts.

        Returns a string with a header, one section per scene
        (including timing, frame count, dialogue if any, and any
        Facts correlated to that scene via `source_frame_path`), and
        a flat "Facts" section listing Fact statements that could not
        be correlated to any scene (see this module's docstring for
        the correlation mechanism and why some facts land here).
        """
        data = self.collect()
        lines = ["# Scene Summary", ""]

        if not data.scenes:
            lines.append("_No scenes found._")
        else:
            lines.append(f"**{len(data.scenes)} scenes detected**")
            lines.append("")

            for i, scene in enumerate(data.scenes, 1):
                lines.append(f"## Scene {i}")
                lines.append("")
                lines.append(
                    f"- **Time**: {scene.start_seconds:.2f}s – {scene.end_seconds:.2f}s"
                )
                lines.append(f"- **Frames**: {scene.frame_count}")
                lines.append(
                    f"- **Transcript segments**: {scene.transcript_segment_count}"
                )
                if scene.dialogue:
                    lines.append("")
                    lines.append(f"> {scene.dialogue}")
                if scene.facts:
                    lines.append("")
                    lines.append("**Facts observed:**")
                    for fact in scene.facts:
                        lines.append(f"- {fact.statement}")
                lines.append("")

        if data.facts:
            lines.append("## Facts")
            lines.append("")
            lines.append(
                f"**{len(data.facts)} facts extracted** "
                "(not yet correlated to specific scenes)"
            )
            lines.append("")
            for fact in data.facts:
                lines.append(f"- {fact.statement}")
            lines.append("")

        return "\n".join(lines)

    def generate(self) -> tuple[SceneSummaryData, str]:
        """
        Convenience method: returns both structured data and Markdown.

        Returns:
            Tuple of (SceneSummaryData, markdown string).
        """
        data = self.collect()
        markdown = self.render_markdown()
        return data, markdown
