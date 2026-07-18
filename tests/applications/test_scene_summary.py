"""Tests for SceneSummary application."""

from __future__ import annotations

from uuid import uuid4

from sceneforge.applications.scene_summary import SceneSummary, SceneSummaryData
from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.storage import InMemoryEntityStore


def _make_scene_entity(
    scene_index: int = 0,
    start: float = 0.0,
    end: float = 2.0,
    frame_paths: list[str] | None = None,
    transcript_segment_count: int = 0,
    payload: str | None = None,
) -> Entity[str | None]:
    """Create a SceneEntity with realistic metadata."""
    return Entity(
        kind=EntityKind.SCENE,
        builder="scene_grouping",
        payload=payload,
        metadata={
            "media_id": str(uuid4()),
            "scene_index": scene_index,
            "start_seconds": start,
            "end_seconds": end,
            "frame_paths": frame_paths or [],
            "transcript_segment_count": transcript_segment_count,
        },
    )


def test_scene_summary_construction() -> None:
    """SceneSummary accepts an InMemoryEntityStore."""
    store = InMemoryEntityStore()
    summary = SceneSummary(store)
    assert summary is not None


def test_scene_summary_empty_store() -> None:
    """Empty store returns empty SceneSummaryData."""
    store = InMemoryEntityStore()
    summary = SceneSummary(store)
    data = summary.collect()
    assert isinstance(data, SceneSummaryData)
    assert data.scenes == ()


def test_scene_summary_collect_returns_structured_data() -> None:
    """collect() returns SceneSummaryData with SceneData tuples."""
    store = InMemoryEntityStore()
    entity = _make_scene_entity(
        scene_index=0,
        start=0.0,
        end=5.0,
        frame_paths=["a.png", "b.png"],
        transcript_segment_count=2,
        payload="Hello world",
    )
    store.put("scene:0", [entity])

    summary = SceneSummary(store)
    data = summary.collect()

    assert len(data.scenes) == 1
    scene = data.scenes[0]
    assert scene.scene_index == 0
    assert scene.start_seconds == 0.0
    assert scene.end_seconds == 5.0
    assert scene.frame_count == 2
    assert scene.transcript_segment_count == 2
    assert scene.dialogue == "Hello world"


def test_scene_summary_collect_multiple_scenes() -> None:
    """collect() handles multiple scenes sorted by scene_index."""
    store = InMemoryEntityStore()
    scene1 = _make_scene_entity(scene_index=1, start=2.0, end=4.0)
    scene0 = _make_scene_entity(scene_index=0, start=0.0, end=2.0)
    store.put("scene:1", [scene1])
    store.put("scene:0", [scene0])

    summary = SceneSummary(store)
    data = summary.collect()

    assert len(data.scenes) == 2
    assert data.scenes[0].scene_index == 0
    assert data.scenes[1].scene_index == 1


def test_scene_summary_render_markdown_empty() -> None:
    """render_markdown() produces valid output for empty store."""
    store = InMemoryEntityStore()
    summary = SceneSummary(store)
    markdown = summary.render_markdown()

    assert isinstance(markdown, str)
    assert "# Scene Summary" in markdown


def test_scene_summary_render_markdown_with_content() -> None:
    """render_markdown() produces valid markdown with scene data."""
    store = InMemoryEntityStore()
    entity = _make_scene_entity(
        scene_index=0,
        start=0.0,
        end=5.0,
        frame_paths=["frame.png"],
        transcript_segment_count=1,
        payload="Test dialogue",
    )
    store.put("scene:0", [entity])

    summary = SceneSummary(store)
    markdown = summary.render_markdown()

    assert "## Scene 1" in markdown
    assert "0.00s" in markdown
    assert "5.00s" in markdown
    assert "**Frames**: 1" in markdown
    assert "Test dialogue" in markdown


def test_scene_summary_generate_convenience() -> None:
    """generate() returns both data and markdown."""
    store = InMemoryEntityStore()
    entity = _make_scene_entity(
        scene_index=0,
        start=0.0,
        end=2.0,
        frame_paths=["f.png"],
        transcript_segment_count=0,
        payload="Hi",
    )
    store.put("scene:0", [entity])

    summary = SceneSummary(store)
    data, markdown = summary.generate()

    assert isinstance(data, SceneSummaryData)
    assert isinstance(markdown, str)
    assert len(data.scenes) == 1


def test_scene_summary_dialogue_none_when_empty() -> None:
    """SceneData.dialogue is None when entity payload is None."""
    store = InMemoryEntityStore()
    entity = _make_scene_entity(
        scene_index=0,
        start=0.0,
        end=2.0,
        frame_paths=[],
        transcript_segment_count=0,
        payload=None,
    )
    store.put("scene:0", [entity])

    summary = SceneSummary(store)
    data = summary.collect()

    assert data.scenes[0].dialogue is None


def test_scene_summary_frame_count_from_list() -> None:
    """frame_count uses len() on frame_paths list."""
    store = InMemoryEntityStore()
    entity = _make_scene_entity(
        scene_index=0,
        start=0.0,
        end=2.0,
        frame_paths=["a.png", "b.png", "c.png"],
        transcript_segment_count=0,
    )
    store.put("scene:0", [entity])

    summary = SceneSummary(store)
    data = summary.collect()

    assert data.scenes[0].frame_count == 3
