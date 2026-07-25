"""
Tests for TransformersCaptionProvider.

These never download model weights, touch the network, or need
`torch` installed -- they inject a fake pipeline satisfying
`ImageTextToTextPipelineProtocol`, which is the entire point of that
Protocol existing (see the module docstring in
`sceneforge/contrib/transformers_caption/provider.py`). A separate,
explicitly network-free contract test checks that the *real*
`transformers.Pipeline.__call__` signature matches what this provider
expects, without instantiating a real pipeline (which would try to
download weights).
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from sceneforge.contrib.transformers_caption import (
    CaptionArtifact,
    TransformersCaptionProvider,
)
from sceneforge.core.artifact import ArtifactKind
from sceneforge.core.async_pipeline import AsyncPipeline
from sceneforge.core.async_provider import SyncProviderAdapter
from sceneforge.core.exceptions import ProviderError
from sceneforge.core.pipeline import Pipeline
from sceneforge.media.audio import AudioMedia
from sceneforge.media.image import ImageMedia


class FakeCaptionPipeline:
    """Satisfies ImageTextToTextPipelineProtocol without any real model weights."""

    def __init__(self, caption: str = "a photo of a cat") -> None:
        self._caption = caption
        self.calls: list[tuple[str, str | None, dict]] = []

    def __call__(self, images, text=None, **kwargs):
        self.calls.append((images, text, kwargs))
        return [{"generated_text": self._caption}]


class BrokenCaptionPipeline:
    def __call__(self, images, text=None, **kwargs):
        raise RuntimeError("model inference failed")


class EmptyResultCaptionPipeline:
    def __call__(self, images, text=None, **kwargs):
        return []


def _image(source: str = "/tmp/frame.png") -> ImageMedia:
    return ImageMedia(
        name="frame.png",
        width=224,
        height=224,
        fmt="PNG",
        metadata={"source": source},
    )


def test_caption_produces_one_artifact():
    pipe = FakeCaptionPipeline(" A dog running on the beach. ")
    provider = TransformersCaptionProvider(pipe)

    artifacts = provider.run(_image())

    assert len(artifacts) == 1
    assert isinstance(artifacts[0], CaptionArtifact)
    assert artifacts[0].kind == ArtifactKind.CAPTION
    assert artifacts[0].payload == "A dog running on the beach."  # stripped


def test_caption_passes_source_path_to_pipeline():
    pipe = FakeCaptionPipeline()
    provider = TransformersCaptionProvider(pipe)

    provider.run(_image(source="/tmp/my_frame.png"))

    assert pipe.calls[0][0] == "/tmp/my_frame.png"


def test_source_frame_path_is_recorded_on_the_artifact():
    """Regression test: this field existed on CaptionArtifact but was
    never populated until noticed while adding
    TransformersObjectDetectionProvider (same gap existed there)."""
    provider = TransformersCaptionProvider(FakeCaptionPipeline())

    artifacts = provider.run(_image(source="/tmp/my_frame.png"))

    assert artifacts[0].source_frame_path == "/tmp/my_frame.png"


def test_prompt_is_forwarded_as_text_argument():
    pipe = FakeCaptionPipeline()
    provider = TransformersCaptionProvider(pipe, prompt="a photo of")

    provider.run(_image())

    assert pipe.calls[0][1] == "a photo of"


def test_prompt_is_recorded_on_the_artifact():
    pipe = FakeCaptionPipeline()
    provider = TransformersCaptionProvider(pipe, prompt="a photo of")

    artifacts = provider.run(_image())

    assert artifacts[0].prompt == "a photo of"


def test_generate_kwargs_are_forwarded():
    pipe = FakeCaptionPipeline()
    provider = TransformersCaptionProvider(pipe, max_new_tokens=20, num_beams=3)

    provider.run(_image())

    assert pipe.calls[0][2] == {"max_new_tokens": 20, "num_beams": 3}


def test_no_prompt_by_default():
    pipe = FakeCaptionPipeline()
    provider = TransformersCaptionProvider(pipe)

    provider.run(_image())

    assert pipe.calls[0][1] is None


def test_non_image_media_raises_type_error():
    provider = TransformersCaptionProvider(FakeCaptionPipeline())
    audio = AudioMedia(name="clip.wav", duration=1.0, sample_rate=16000, channels=1)

    with pytest.raises(TypeError):
        provider.run(audio)


def test_missing_source_raises_provider_error():
    provider = TransformersCaptionProvider(FakeCaptionPipeline())
    media = ImageMedia(name="frame.png", width=1, height=1, fmt="PNG")

    with pytest.raises(ProviderError):
        provider.run(media)


def test_pipeline_exception_is_wrapped_in_provider_error():
    provider = TransformersCaptionProvider(BrokenCaptionPipeline())

    with pytest.raises(ProviderError):
        provider.run(_image())


def test_empty_result_raises_provider_error():
    provider = TransformersCaptionProvider(EmptyResultCaptionPipeline())

    with pytest.raises(ProviderError):
        provider.run(_image())


def test_two_differently_configured_instances_have_different_fingerprints():
    plain = TransformersCaptionProvider(FakeCaptionPipeline())
    prompted = TransformersCaptionProvider(FakeCaptionPipeline(), prompt="a photo of")

    assert plain.execution_fingerprint != prompted.execution_fingerprint


def test_works_through_sync_pipeline():
    pipe = FakeCaptionPipeline()
    pipeline = Pipeline(provider=TransformersCaptionProvider(pipe))

    result = pipeline.run_detailed(_image())

    assert len(result.artifacts) == 1
    assert result.from_cache is False


def test_sync_provider_adapter_works_through_async_pipeline_batch():
    """
    The whole reason TransformersCaptionProvider is synchronous rather
    than duplicated as an async implementation: SyncProviderAdapter
    should compose with AsyncPipeline.run_many().
    """

    class ImmediateExecutorLoop:
        def run_in_executor(self, executor, function, media):
            async def _invoke():
                return function(media)

            return _invoke()

    async def _run():
        pipe = FakeCaptionPipeline()
        adapter = SyncProviderAdapter(TransformersCaptionProvider(pipe))
        pipeline = AsyncPipeline(provider=adapter, max_concurrency=2)

        frames = [_image(source=f"/tmp/frame_{i}.png") for i in range(4)]
        return await pipeline.run_many(frames)

    with patch(
        "sceneforge.core.async_provider.asyncio.get_running_loop",
        return_value=ImmediateExecutorLoop(),
    ):
        batch = asyncio.run(_run())
    assert batch.all_succeeded
    assert len(batch.successes) == 4


def test_real_transformers_pipeline_shape_is_compatible():
    """
    Contract check only -- never instantiates a real pipeline (which
    would try to download weights and typically needs `torch`) or runs
    inference. Confirms ImageTextToTextPipelineProtocol was modeled on
    the real, currently-installed library's actual class, not a guess.
    """
    transformers = pytest.importorskip("transformers")

    assert hasattr(transformers, "Pipeline")
    assert transformers.Pipeline.__call__ is not None
