"""
SceneForge Scene Summary Application

A simple, first-pass application that demonstrates the framework's
application layer pattern. Reads scene entities from an EntityStore,
collects structured data, and renders a human-readable Markdown summary.

This is intentionally minimal -- it exists to prove the framework's
success definition: that applications can be built on top of the
knowledge layer without modifying any core components.

Also renders `Fact`-kind Entities (real since `FactExtractionBuilder`,
`sceneforge/knowledge/fact_extraction_builder.py`) as their own
section, independent of scenes. Facts and Scenes are not correlated
here -- a Fact's `media_id` is whatever image it was captioned from
(typically an extracted frame), which is not the same media a
`SceneCutArtifact`'s `media_id` refers to (the source video), and
nothing yet maps one to the other the way `SceneFaceBuilder`/
`SceneTextBuilder` correlate via `source_frame_path` (ADR-0016). Adding
that correlation here would be inventing a new cross-domain
correlation mechanism speculatively, ahead of any real need for it --
exactly what this project's own discipline argues against. Facts are
rendered as a flat list instead, honestly reflecting what the data
actually supports today.
"""

from __future__ import annotations

from dataclasses import dataclass

from sceneforge.knowledge.entity import EntityKind
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


@dataclass(frozen=True, slots=True)
class FactData:
    """Structured data for a single Fact."""

    statement: str
    media_id: str
    source_provider: str | None
    prompt: str | None


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
        metadata keys media_id, source_provider, prompt.
        """
        scenes: list[SceneData] = []
        facts: list[FactData] = []
        for entity in iter_all_entities(self._store):
            if entity.kind == EntityKind.SCENE:
                meta = entity.metadata
                scenes.append(
                    SceneData(
                        scene_index=meta.get("scene_index", 0),
                        start_seconds=meta.get("start_seconds", 0.0),
                        end_seconds=meta.get("end_seconds", 0.0),
                        frame_count=len(meta.get("frame_paths", [])),
                        transcript_segment_count=meta.get(
                            "transcript_segment_count", 0
                        ),
                        dialogue=entity.payload,
                    )
                )
            elif entity.kind == EntityKind.FACT:
                meta = entity.metadata
                if not entity.payload:
                    continue
                facts.append(
                    FactData(
                        statement=entity.payload,
                        media_id=meta.get("media_id", ""),
                        source_provider=meta.get("source_provider"),
                        prompt=meta.get("prompt"),
                    )
                )
        scenes.sort(key=lambda s: s.scene_index)
        return SceneSummaryData(scenes=tuple(scenes), facts=tuple(facts))

    def render_markdown(self) -> str:
        """
        Render a Markdown summary of all scenes and facts.

        Returns a string with a header, one section per scene
        (including timing, frame count, and dialogue if any), and a
        flat "Facts" section listing every Fact statement (not
        correlated to scenes -- see this module's docstring for why).
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
