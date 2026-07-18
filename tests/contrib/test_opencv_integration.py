"""
Integration tests for the OpenCV contrib package.

These exercise the real `cv2.CascadeClassifier` and real image
decoding against real generated image files -- not mocked. There is
no real face photograph available in this environment (no network
access to fetch one), so the positive-detection claim is documented
as real-but-unverified-here in the provider's module docstring; these
tests prove the mechanics and the negative path with certainty.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("cv2")
import numpy as np  # noqa: E402

from sceneforge.contrib.opencv import (  # noqa: E402
    FaceDetectionArtifact,
    OpenCVFaceDetectionProvider,
    OpenCVImageEnricher,
)
from sceneforge.core.artifact import ArtifactKind  # noqa: E402
from sceneforge.core.exceptions import EnrichmentError, ProviderError  # noqa: E402
from sceneforge.core.pipeline import Pipeline  # noqa: E402
from sceneforge.media.image_loader import LocalImageLoader  # noqa: E402


def _write_solid_image(path: Path, width: int = 200, height: int = 150) -> Path:
    """A real PNG file: solid gray. Real bytes, decoded by real OpenCV."""
    import cv2

    image = np.full((height, width, 3), 128, dtype=np.uint8)
    cv2.imwrite(str(path), image)
    return path


@pytest.fixture
def solid_image(tmp_path: Path) -> Path:
    return _write_solid_image(tmp_path / "solid.png")


def test_local_image_loader_produces_placeholder_dimensions(solid_image: Path):
    """Sanity check on the pre-enrichment state OpenCVImageEnricher fixes."""
    media = LocalImageLoader(solid_image).load()
    assert media.width == 0
    assert media.height == 0
    assert media.metadata["source"] == str(solid_image)


def test_image_enricher_fills_in_real_dimensions(solid_image: Path):
    media = LocalImageLoader(solid_image).load()
    enriched = OpenCVImageEnricher().enrich(media)

    assert enriched is not media
    assert enriched.id == media.id
    assert enriched.width == 200
    assert enriched.height == 150


def test_image_enricher_raises_on_undecodable_file(tmp_path: Path):
    bad_path = tmp_path / "not_really_an_image.png"
    bad_path.write_bytes(b"this is not image data")
    from sceneforge.media.image import ImageMedia

    fake_media = ImageMedia(
        name="bad.png", width=0, height=0, fmt="PNG", metadata={"source": str(bad_path)}
    )

    with pytest.raises(EnrichmentError):
        OpenCVImageEnricher().enrich(fake_media)


def test_face_detection_on_solid_image_finds_nothing(solid_image: Path):
    """The certain negative case: a real cascade, on a real image, with no face."""
    media = LocalImageLoader(solid_image).load()
    enriched = OpenCVImageEnricher().enrich(media)

    artifacts = OpenCVFaceDetectionProvider().run(enriched)

    assert artifacts == []


def test_face_detection_artifact_shape_when_synthetically_forced(tmp_path: Path):
    """
    Can't get a real cascade to find a face in a synthetic image (Haar
    cascades need real photographic gradients -- verified manually
    during development, a hand-drawn face does not trigger detection).
    This test instead proves FaceDetectionArtifact's shape directly,
    since the provider's artifact-building code path is otherwise only
    exercised by the (currently always-empty, in this sandbox) real
    detection loop.
    """
    from uuid import uuid4

    artifact = FaceDetectionArtifact(
        media_id=uuid4(),
        provider="opencv_face_detection",
        x=10,
        y=20,
        width=50,
        height=60,
    )
    assert artifact.kind == ArtifactKind.FACE_DETECTION
    assert (artifact.x, artifact.y, artifact.width, artifact.height) == (10, 20, 50, 60)


def test_full_pipeline_with_enricher_and_real_provider(solid_image: Path):
    media = LocalImageLoader(solid_image).load()
    pipeline = Pipeline(
        provider=OpenCVFaceDetectionProvider(), enricher=OpenCVImageEnricher()
    )

    result = pipeline.run_detailed(media)

    assert result.artifacts == []  # correct: no faces in a solid-color image
    assert result.media.width == 200  # proves enrichment ran before the provider


def test_missing_source_raises_provider_error():
    from sceneforge.media.image import ImageMedia

    media = ImageMedia(name="x.png", width=10, height=10, fmt="PNG")
    with pytest.raises(ProviderError):
        OpenCVFaceDetectionProvider().run(media)


def test_non_image_media_raises_type_error():
    from sceneforge.media.audio import AudioMedia

    provider = OpenCVFaceDetectionProvider()
    audio = AudioMedia(name="x.wav", duration=1.0, sample_rate=16000, channels=1)
    with pytest.raises(TypeError):
        provider.run(audio)


def test_enricher_ignores_non_image_media():
    from sceneforge.media.audio import AudioMedia

    media = AudioMedia(name="x.wav", duration=1.0, sample_rate=16000, channels=1)
    result = OpenCVImageEnricher().enrich(media)
    assert result is media
