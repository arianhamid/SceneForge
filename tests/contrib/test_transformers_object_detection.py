"""
Tests for TransformersObjectDetectionProvider.

Same reasoning as tests/contrib/test_transformers_caption.py: no
network access, no downloaded weights, no torch required -- a fake
pipeline satisfying ObjectDetectionPipelineProtocol stands in for the
real one, plus a contract test confirming the real installed
transformers class shape without instantiating it.
"""

from __future__ import annotations

import pytest

from sceneforge.contrib.transformers_object_detection import (
    ObjectDetectionArtifact,
    TransformersObjectDetectionProvider,
)
from sceneforge.core.artifact import ArtifactKind
from sceneforge.core.exceptions import ProviderError
from sceneforge.core.pipeline import Pipeline
from sceneforge.media.audio import AudioMedia
from sceneforge.media.image import ImageMedia


class FakeDetectionPipeline:
    """Satisfies ObjectDetectionPipelineProtocol without real model weights."""

    def __init__(self, detections=None) -> None:
        self._detections = (
            detections
            if detections is not None
            else [
                {
                    "score": 0.99,
                    "label": "bird",
                    "box": {"xmin": 1, "ymin": 2, "xmax": 3, "ymax": 4},
                },
                {
                    "score": 0.85,
                    "label": "cat",
                    "box": {"xmin": 5, "ymin": 6, "xmax": 7, "ymax": 8},
                },
            ]
        )
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, images, **kwargs):
        self.calls.append((images, kwargs))
        return self._detections


class BrokenDetectionPipeline:
    def __call__(self, images, **kwargs):
        raise RuntimeError("model inference failed")


def _image(source: str = "/tmp/frame.png") -> ImageMedia:
    return ImageMedia(
        name="frame.png",
        width=224,
        height=224,
        fmt="PNG",
        metadata={"source": source},
    )


def test_detection_produces_one_artifact_per_detection():
    provider = TransformersObjectDetectionProvider(FakeDetectionPipeline())

    artifacts = provider.run(_image())

    assert len(artifacts) == 2
    assert all(isinstance(a, ObjectDetectionArtifact) for a in artifacts)
    assert all(a.kind == ArtifactKind.OBJECT_DETECTION for a in artifacts)


def test_detection_fields_are_populated_correctly():
    provider = TransformersObjectDetectionProvider(FakeDetectionPipeline())

    artifacts = provider.run(_image())

    first = artifacts[0]
    assert first.label == "bird"
    assert first.score == 0.99
    assert (first.x_min, first.y_min, first.x_max, first.y_max) == (1, 2, 3, 4)
    assert first.detection_index == 0
    assert artifacts[1].detection_index == 1


def test_empty_detections_is_not_an_error():
    """The real design difference a second real case surfaced: unlike
    captioning, zero detections is a legitimate result, not a failure."""
    provider = TransformersObjectDetectionProvider(FakeDetectionPipeline(detections=[]))

    artifacts = provider.run(_image())

    assert artifacts == []


def test_source_path_is_passed_to_pipeline():
    pipe = FakeDetectionPipeline()
    provider = TransformersObjectDetectionProvider(pipe)

    provider.run(_image(source="/tmp/my_frame.png"))

    assert pipe.calls[0][0] == "/tmp/my_frame.png"


def test_source_frame_path_is_recorded_on_each_artifact():
    """Regression test: this field existed but was never populated until
    caught while writing the end-to-end example script."""
    provider = TransformersObjectDetectionProvider(FakeDetectionPipeline())

    artifacts = provider.run(_image(source="/tmp/my_frame.png"))

    assert all(a.source_frame_path == "/tmp/my_frame.png" for a in artifacts)


def test_threshold_is_forwarded():
    pipe = FakeDetectionPipeline()
    provider = TransformersObjectDetectionProvider(pipe, threshold=0.9)

    provider.run(_image())

    assert pipe.calls[0][1]["threshold"] == 0.9


def test_no_threshold_key_by_default():
    pipe = FakeDetectionPipeline()
    provider = TransformersObjectDetectionProvider(pipe)

    provider.run(_image())

    assert "threshold" not in pipe.calls[0][1]


def test_detect_kwargs_are_forwarded():
    pipe = FakeDetectionPipeline()
    provider = TransformersObjectDetectionProvider(pipe, timeout=5.0)

    provider.run(_image())

    assert pipe.calls[0][1]["timeout"] == 5.0


def test_non_image_media_raises_type_error():
    provider = TransformersObjectDetectionProvider(FakeDetectionPipeline())
    audio = AudioMedia(name="clip.wav", duration=1.0, sample_rate=16000, channels=1)

    with pytest.raises(TypeError):
        provider.run(audio)


def test_missing_source_raises_provider_error():
    provider = TransformersObjectDetectionProvider(FakeDetectionPipeline())
    media = ImageMedia(name="frame.png", width=1, height=1, fmt="PNG")

    with pytest.raises(ProviderError):
        provider.run(media)


def test_pipeline_exception_is_wrapped_in_provider_error():
    provider = TransformersObjectDetectionProvider(BrokenDetectionPipeline())

    with pytest.raises(ProviderError):
        provider.run(_image())


def test_two_differently_configured_instances_have_different_fingerprints():
    plain = TransformersObjectDetectionProvider(FakeDetectionPipeline())
    thresholded = TransformersObjectDetectionProvider(
        FakeDetectionPipeline(), threshold=0.9
    )

    assert plain.execution_fingerprint != thresholded.execution_fingerprint


def test_works_through_sync_pipeline():
    provider = TransformersObjectDetectionProvider(FakeDetectionPipeline())
    pipeline = Pipeline(provider=provider)

    result = pipeline.run_detailed(_image())

    assert len(result.artifacts) == 2
    assert result.from_cache is False


def test_real_transformers_pipeline_shape_is_compatible():
    """Contract check only -- never instantiates a real pipeline (which
    would try to download weights and typically needs torch)."""
    transformers = pytest.importorskip("transformers")

    assert hasattr(transformers, "Pipeline")
    assert transformers.Pipeline.__call__ is not None
