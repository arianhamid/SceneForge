"""
Integration tests for the Tesseract OCR contrib package.

Unlike WhisperTranscribeProvider (real weights need network access)
and OpenCVFaceDetectionProvider (no real face photo available here),
this provider's positive-detection claim is genuinely verified: a real
image with real rendered text, read by the real Tesseract binary with
its real bundled English language data. No network access needed --
`tesseract-ocr` ships `eng.traineddata` as part of the system package.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

pytest.importorskip("pytesseract")
pytest.importorskip("PIL")

TESSERACT_AVAILABLE = shutil.which("tesseract") is not None
pytestmark = pytest.mark.skipif(
    not TESSERACT_AVAILABLE, reason="tesseract binary not available on PATH"
)

from sceneforge.contrib.tesseract import (  # noqa: E402
    OCRTextArtifact,
    TesseractOCRProvider,
)
from sceneforge.core.artifact import ArtifactCategory, ArtifactKind  # noqa: E402
from sceneforge.core.exceptions import ProviderError  # noqa: E402
from sceneforge.core.pipeline import Pipeline  # noqa: E402
from sceneforge.media.image_loader import LocalImageLoader  # noqa: E402


def _render_text_image(
    path: Path, text: str, size: tuple[int, int] = (400, 100)
) -> Path:
    """A real image file with real rendered text, using a bundled system font."""
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", size, color="white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32
    )
    draw.text((10, 20), text, fill="black", font=font)
    image.save(path)
    return path


@pytest.fixture
def text_image(tmp_path: Path) -> Path:
    return _render_text_image(tmp_path / "text.png", "HELLO")


@pytest.fixture
def blank_image(tmp_path: Path) -> Path:
    from PIL import Image

    path = tmp_path / "blank.png"
    Image.new("RGB", (200, 100), color="white").save(path)
    return path


def test_real_ocr_reads_real_rendered_text(text_image: Path):
    """The positive case: real text, really read back correctly."""
    media = LocalImageLoader(text_image).load()

    artifacts = TesseractOCRProvider().run(media)

    assert len(artifacts) == 1
    assert artifacts[0].payload == "HELLO"
    assert artifacts[0].kind == ArtifactKind.OCR
    assert artifacts[0].category == ArtifactCategory.RECOGNITION
    assert artifacts[0].confidence > 0


def test_ocr_bounding_box_is_within_image_bounds(text_image: Path):
    media = LocalImageLoader(text_image).load()
    artifact = TesseractOCRProvider().run(media)[0]

    assert 0 <= artifact.x < 400
    assert 0 <= artifact.y < 100
    assert artifact.width > 0
    assert artifact.height > 0


def test_ocr_on_blank_image_finds_nothing(blank_image: Path):
    """The certain negative case: real OCR, on a real image, with no text."""
    media = LocalImageLoader(blank_image).load()

    artifacts = TesseractOCRProvider().run(media)

    assert artifacts == []


def test_multi_word_text_produces_multiple_artifacts(tmp_path: Path):
    path = _render_text_image(tmp_path / "multi.png", "HELLO WORLD")
    media = LocalImageLoader(path).load()

    artifacts = TesseractOCRProvider().run(media)

    words = [a.payload for a in artifacts]
    assert words == ["HELLO", "WORLD"]
    assert [a.word_index for a in artifacts] == [0, 1]


def test_min_confidence_filters_low_confidence_results(text_image: Path):
    media = LocalImageLoader(text_image).load()

    strict = TesseractOCRProvider(min_confidence=101.0).run(media)

    assert strict == []


def test_source_frame_path_set_from_image_metadata(text_image: Path):
    media = LocalImageLoader(text_image).load()
    artifact = TesseractOCRProvider().run(media)[0]

    assert artifact.source_frame_path == str(text_image)


def test_full_pipeline_with_real_provider(text_image: Path):
    media = LocalImageLoader(text_image).load()
    pipeline = Pipeline(provider=TesseractOCRProvider())

    result = pipeline.run_detailed(media)

    assert len(result.artifacts) == 1
    assert result.artifacts[0].payload == "HELLO"
    assert isinstance(result.artifacts[0], OCRTextArtifact)


def test_missing_source_raises_provider_error():
    from sceneforge.media.image import ImageMedia

    media = ImageMedia(name="x.png", width=10, height=10, fmt="PNG")
    with pytest.raises(ProviderError):
        TesseractOCRProvider().run(media)


def test_non_image_media_raises_type_error():
    from sceneforge.media.audio import AudioMedia

    provider = TesseractOCRProvider()
    audio = AudioMedia(name="x.wav", duration=1.0, sample_rate=16000, channels=1)
    with pytest.raises(TypeError):
        provider.run(audio)
