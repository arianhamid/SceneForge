"""
SceneForge Scene Summary Application

A simple, first-pass application that demonstrates the framework's
application layer pattern. Reads scene entities from an EntityStore,
collects structured data, and renders a human-readable Markdown summary.

This is intentionally minimal -- it exists to prove the framework's
success definition: that applications can be built on top of the
knowledge layer without modifying any core components.
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
class SceneSummaryData:
    """Structured summary of all scenes."""

    scenes: tuple[SceneData, ...] = ()


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
        Collect all scene entities from the store and return structured data.

        Reads metadata keys: scene_index, start_seconds, end_seconds,
        frame_paths, transcript_segment_count. Uses entity.payload for
        dialogue text.
        """
        scenes: list[SceneData] = []
        for entity in iter_all_entities(self._store):
            if entity.kind != EntityKind.SCENE:
                continue
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
        scenes.sort(key=lambda s: s.scene_index)
        return SceneSummaryData(scenes=tuple(scenes))

    def render_markdown(self) -> str:
        """
        Render a Markdown summary of all scenes.

        Returns a string with a header and one section per scene,
        including timing, frame count, and dialogue (if any).
        """
        data = self.collect()
        lines = ["# Scene Summary", ""]

        if not data.scenes:
            lines.append("_No scenes found._")
            return "\n".join(lines)

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
