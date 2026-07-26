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


def _make_fact_entity(
    statement: str = "a cat sitting on a windowsill",
    media_id: str | None = None,
    source_provider: str = "transformers_caption",
    prompt: str | None = None,
    source_frame_path: str = "",
) -> Entity[str]:
    """Create a FACT Entity with realistic metadata, matching what
    FactExtractionBuilder actually produces."""
    return Entity(
        kind=EntityKind.FACT,
        builder="fact_extraction",
        payload=statement,
        metadata={
            "media_id": media_id or str(uuid4()),
            "statement_type": "caption",
            "source_provider": source_provider,
            "prompt": prompt,
            "source_frame_path": source_frame_path,
        },
    )


def test_scene_summary_empty_store_has_no_facts() -> None:
    store = InMemoryEntityStore()
    summary = SceneSummary(store)
    data = summary.collect()
    assert data.facts == ()


def test_scene_summary_collects_facts() -> None:
    store = InMemoryEntityStore()
    store.put("fact:0", [_make_fact_entity("a dog runs on the beach")])

    summary = SceneSummary(store)
    data = summary.collect()

    assert len(data.facts) == 1
    assert data.facts[0].statement == "a dog runs on the beach"
    assert data.facts[0].source_provider == "transformers_caption"


def test_scene_summary_collects_multiple_facts():
    store = InMemoryEntityStore()
    store.put(
        "facts",
        [
            _make_fact_entity("a dog runs"),
            _make_fact_entity("a bird flies"),
        ],
    )

    summary = SceneSummary(store)
    data = summary.collect()

    assert {f.statement for f in data.facts} == {"a dog runs", "a bird flies"}


def test_scene_summary_ignores_facts_with_empty_payload():
    store = InMemoryEntityStore()
    store.put("fact:0", [_make_fact_entity("")])

    summary = SceneSummary(store)
    data = summary.collect()

    assert data.facts == ()


def test_scene_summary_scenes_and_facts_do_not_interfere():
    store = InMemoryEntityStore()
    store.put(
        "mixed",
        [
            _make_scene_entity(scene_index=0, payload="dialogue"),
            _make_fact_entity("a cat"),
        ],
    )

    summary = SceneSummary(store)
    data = summary.collect()

    assert len(data.scenes) == 1
    assert len(data.facts) == 1


def test_render_markdown_includes_facts_section():
    store = InMemoryEntityStore()
    store.put("fact:0", [_make_fact_entity("a sunset over the ocean")])

    summary = SceneSummary(store)
    markdown = summary.render_markdown()

    assert "## Facts" in markdown
    assert "a sunset over the ocean" in markdown
    assert "1 facts extracted" in markdown


def test_render_markdown_omits_facts_section_when_there_are_none():
    store = InMemoryEntityStore()
    store.put("scene:0", [_make_scene_entity(scene_index=0)])

    summary = SceneSummary(store)
    markdown = summary.render_markdown()

    assert "## Facts" not in markdown


def test_render_markdown_still_reports_no_scenes_found_with_only_facts():
    store = InMemoryEntityStore()
    store.put("fact:0", [_make_fact_entity("a lonely fact with no scenes")])

    summary = SceneSummary(store)
    markdown = summary.render_markdown()

    assert "_No scenes found._" in markdown
    assert "a lonely fact with no scenes" in markdown


def test_scene_summary_data_default_facts_is_empty_tuple():
    assert SceneSummaryData().facts == ()


def test_fact_correlates_to_scene_via_source_frame_path():
    """A Fact whose source_frame_path matches a scene's frame_paths is
    attached only to that scene, even when scene indices repeat."""
    store = InMemoryEntityStore()
    store.put(
        "mixed",
        [
            _make_scene_entity(
                scene_index=0,
                frame_paths=["other_video_frame.png"],
                payload="other video",
            ),
            _make_scene_entity(
                scene_index=0,
                frame_paths=["frame_001.png"],
                payload="matched video",
            ),
            _make_fact_entity(
                "a cat sitting on a windowsill",
                source_frame_path="frame_001.png",
            ),
        ],
    )

    summary = SceneSummary(store)
    data = summary.collect()

    assert data.facts == ()
    scenes_by_dialogue = {scene.dialogue: scene for scene in data.scenes}
    assert scenes_by_dialogue["other video"].facts == ()
    matched_facts = scenes_by_dialogue["matched video"].facts
    assert len(matched_facts) == 1
    assert matched_facts[0].statement == "a cat sitting on a windowsill"
    assert matched_facts[0].scene_index == 0


def test_fact_with_no_matching_frame_path_stays_uncorrelated():
    """A Fact whose source_frame_path matches no known scene frame
    stays in the flat facts list, same as one with no path at all."""
    store = InMemoryEntityStore()
    store.put(
        "mixed",
        [
            _make_scene_entity(scene_index=0, frame_paths=["frame_001.png"]),
            _make_fact_entity("an unrelated fact", source_frame_path="frame_999.png"),
        ],
    )

    summary = SceneSummary(store)
    data = summary.collect()

    assert len(data.facts) == 1
    assert data.facts[0].statement == "an unrelated fact"
    assert data.facts[0].scene_index is None
    assert data.scenes[0].facts == ()


def test_facts_split_across_correlated_and_uncorrelated():
    """A mix of correlated and uncorrelated facts lands in the right
    place, and correlated facts never also appear in the flat list."""
    store = InMemoryEntityStore()
    store.put(
        "mixed",
        [
            _make_scene_entity(scene_index=0, frame_paths=["frame_a.png"]),
            _make_fact_entity("in scene", source_frame_path="frame_a.png"),
            _make_fact_entity("not in any scene"),
        ],
    )

    summary = SceneSummary(store)
    data = summary.collect()

    assert [f.statement for f in data.scenes[0].facts] == ["in scene"]
    assert [f.statement for f in data.facts] == ["not in any scene"]


def test_render_markdown_shows_correlated_facts_under_their_scene():
    store = InMemoryEntityStore()
    store.put(
        "mixed",
        [
            _make_scene_entity(scene_index=0, frame_paths=["frame_a.png"]),
            _make_fact_entity(
                "a dog runs on the beach", source_frame_path="frame_a.png"
            ),
        ],
    )

    summary = SceneSummary(store)
    markdown = summary.render_markdown()

    assert "## Scene 1" in markdown
    assert "**Facts observed:**" in markdown
    assert "a dog runs on the beach" in markdown
    assert "## Facts" not in markdown


def test_scene_data_facts_defaults_to_empty_tuple():
    scene = _make_scene_entity(scene_index=0)
    store = InMemoryEntityStore()
    store.put("scene:0", [scene])

    summary = SceneSummary(store)
    data = summary.collect()

    assert data.scenes[0].facts == ()


def test_scene_summary_renders_object_detection_facts_without_modification():
    """SceneSummary was built and tested against caption-derived Facts only.
    This proves it also handles object-detection-derived Facts correctly
    with zero code changes -- real end-to-end, not a hand-built fixture --
    confirming FactExtractionBuilder's shared shape actually holds for
    downstream consumers too, not just for the builder itself."""
    from sceneforge.contrib.transformers_object_detection import (
        ObjectDetectionArtifact,
    )
    from sceneforge.knowledge.fact_extraction_builder import FactExtractionBuilder

    media_id = uuid4()
    detection = ObjectDetectionArtifact(
        media_id=media_id, label="dog", score=0.9, x_min=1, y_min=2, x_max=3, y_max=4
    )
    entities = FactExtractionBuilder().build([detection])
    store = InMemoryEntityStore()
    store.put("facts", entities)

    summary = SceneSummary(store)
    data = summary.collect()
    markdown = summary.render_markdown()

    assert len(data.facts) == 1
    assert data.facts[0].statement == "dog detected"
    assert "dog detected" in markdown
