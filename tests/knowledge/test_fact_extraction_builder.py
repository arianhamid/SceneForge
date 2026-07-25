"""
Tests for FactExtractionBuilder's extraction logic, using hand-built
synthetic CaptionArtifacts -- no real transformers pipeline needed to
verify the extraction itself. See
tests/knowledge/test_fact_extraction_integration.py for the version
that feeds real provider output (through a real Pipeline, with a fake
model injected) through this builder.
"""

from __future__ import annotations

from uuid import uuid4

from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact
from sceneforge.contrib.transformers_caption.caption_artifact import CaptionArtifact
from sceneforge.contrib.transformers_object_detection.object_detection_artifact import (
    ObjectDetectionArtifact,
)
from sceneforge.knowledge.entity import EntityKind
from sceneforge.knowledge.fact_extraction_builder import FactExtractionBuilder


def _caption(media_id, text="a cat sitting on a windowsill", prompt=None):
    return CaptionArtifact(media_id=media_id, payload=text, prompt=prompt)


def _detection(media_id, label="dog", score=0.9, index=0):
    return ObjectDetectionArtifact(
        media_id=media_id,
        label=label,
        score=score,
        x_min=1,
        y_min=2,
        x_max=3,
        y_max=4,
        detection_index=index,
    )


def test_produces_one_fact_entity_per_caption():
    media_id = uuid4()
    builder = FactExtractionBuilder()

    entities = builder.build([_caption(media_id)])

    assert len(entities) == 1
    assert entities[0].kind == EntityKind.FACT
    assert entities[0].payload == "a cat sitting on a windowsill"


def test_produces_one_entity_per_caption_artifact():
    media_id = uuid4()
    builder = FactExtractionBuilder()

    entities = builder.build(
        [_caption(media_id, "a dog runs"), _caption(media_id, "a bird flies")]
    )

    assert len(entities) == 2
    assert {e.payload for e in entities} == {"a dog runs", "a bird flies"}


def test_entity_parents_trace_back_to_the_caption_artifact():
    media_id = uuid4()
    caption = _caption(media_id)
    builder = FactExtractionBuilder()

    entities = builder.build([caption])

    assert entities[0].parents == (caption.id,)


def test_entity_provenance_traces_back_to_the_caption_artifact():
    media_id = uuid4()
    caption = _caption(media_id)
    builder = FactExtractionBuilder()

    entities = builder.build([caption])

    assert entities[0].provenance is not None
    assert entities[0].provenance.builder == "fact_extraction"
    assert entities[0].provenance.source_artifact_ids == (caption.id,)


def test_entity_metadata_records_media_and_prompt():
    media_id = uuid4()
    caption = _caption(media_id, prompt="a photo of")
    builder = FactExtractionBuilder()

    entities = builder.build([caption])

    assert entities[0].metadata["media_id"] == str(media_id)
    assert entities[0].metadata["statement_type"] == "caption"
    assert entities[0].metadata["prompt"] == "a photo of"


def test_caption_fact_metadata_includes_source_frame_path():
    media_id = uuid4()
    caption = CaptionArtifact(
        media_id=media_id, payload="a cat", source_frame_path="/tmp/frame_3.png"
    )
    builder = FactExtractionBuilder()

    entities = builder.build([caption])

    assert entities[0].metadata["source_frame_path"] == "/tmp/frame_3.png"


def test_detection_fact_metadata_includes_source_frame_path():
    media_id = uuid4()
    detection = ObjectDetectionArtifact(
        media_id=media_id,
        label="dog",
        score=0.9,
        source_frame_path="/tmp/frame_7.png",
    )
    builder = FactExtractionBuilder()

    entities = builder.build([detection])

    assert entities[0].metadata["source_frame_path"] == "/tmp/frame_7.png"


def test_empty_caption_produces_no_entity():
    media_id = uuid4()
    builder = FactExtractionBuilder()

    entities = builder.build([_caption(media_id, text="")])

    assert entities == []


def test_ignores_non_caption_artifacts():
    media_id = uuid4()
    builder = FactExtractionBuilder()
    scene_cut = SceneCutArtifact(media_id=media_id, scene_index=0)

    entities = builder.build([scene_cut, _caption(media_id)])

    assert len(entities) == 1
    assert entities[0].kind == EntityKind.FACT


def test_no_captions_produces_no_entities():
    media_id = uuid4()
    builder = FactExtractionBuilder()
    scene_cut = SceneCutArtifact(media_id=media_id, scene_index=0)

    entities = builder.build([scene_cut])

    assert entities == []


def test_empty_artifact_list_produces_no_entities():
    builder = FactExtractionBuilder()
    assert builder.build([]) == []


def test_builder_name_and_version():
    builder = FactExtractionBuilder()
    assert builder.name == "fact_extraction"
    assert builder.version == "1.0.0"


def test_produces_one_fact_entity_per_detection():
    media_id = uuid4()
    builder = FactExtractionBuilder()

    entities = builder.build([_detection(media_id, label="dog")])

    assert len(entities) == 1
    assert entities[0].kind == EntityKind.FACT
    assert entities[0].payload == "dog detected"


def test_detection_entity_traces_back_via_parents_and_provenance():
    media_id = uuid4()
    detection = _detection(media_id)
    builder = FactExtractionBuilder()

    entities = builder.build([detection])

    assert entities[0].parents == (detection.id,)
    assert entities[0].provenance is not None
    assert entities[0].provenance.source_artifact_ids == (detection.id,)


def test_detection_confidence_populates_provenance_confidence():
    media_id = uuid4()
    detection = _detection(media_id, score=0.73)
    builder = FactExtractionBuilder()

    entities = builder.build([detection])

    assert entities[0].provenance.confidence == 0.73


def test_caption_derived_fact_has_no_confidence():
    """Captions have no equivalent confidence score in the pipeline shape
    this project models -- an honest gap, not a guessed number."""
    media_id = uuid4()
    builder = FactExtractionBuilder()

    entities = builder.build([_caption(media_id)])

    assert entities[0].provenance.confidence is None


def test_detection_metadata_records_label_and_bounding_box():
    media_id = uuid4()
    detection = _detection(media_id, label="cat")
    builder = FactExtractionBuilder()

    entities = builder.build([detection])

    meta = entities[0].metadata
    assert meta["media_id"] == str(media_id)
    assert meta["statement_type"] == "object_detection"
    assert meta["label"] == "cat"
    assert meta["bounding_box"] == {"x_min": 1, "y_min": 2, "x_max": 3, "y_max": 4}


def test_detection_with_empty_label_produces_no_entity():
    media_id = uuid4()
    builder = FactExtractionBuilder()

    entities = builder.build([_detection(media_id, label="")])

    assert entities == []


def test_mixed_captions_and_detections_all_produce_facts():
    media_id = uuid4()
    builder = FactExtractionBuilder()

    entities = builder.build(
        [
            _caption(media_id, "a park scene"),
            _detection(media_id, label="dog"),
            _detection(media_id, label="bench", index=1),
        ]
    )

    assert len(entities) == 3
    statement_types = {e.metadata["statement_type"] for e in entities}
    assert statement_types == {"caption", "object_detection"}


def test_multiple_detections_produce_separate_facts():
    media_id = uuid4()
    builder = FactExtractionBuilder()

    entities = builder.build(
        [
            _detection(media_id, label="dog", index=0),
            _detection(media_id, label="cat", index=1),
        ]
    )

    assert {e.payload for e in entities} == {"dog detected", "cat detected"}
