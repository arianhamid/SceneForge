"""
Integration test for SceneTextBuilder against REAL cross-domain
provider output: a real video with real text burned into each half via
ffmpeg's drawtext filter, real frame extraction, real scene detection,
and real Tesseract OCR run against each extracted frame as its own
ImageMedia -- the strongest possible proof of ADR-0016's correlation
pattern, since (unlike the SceneFaceBuilder integration test) there's
no "no real photo available" caveat here: the text really is on
screen, and Tesseract really reads it back correctly, per scene.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from sceneforge.contrib.ffmpeg import FFmpegFrameExtractionProvider, FFprobeEnricher
from sceneforge.contrib.scenedetect import PySceneDetectProvider
from sceneforge.contrib.tesseract import TesseractOCRProvider
from sceneforge.core.pipeline import Pipeline
from sceneforge.knowledge import SceneTextBuilder
from sceneforge.media.image_loader import LocalImageLoader
from sceneforge.media.video_loader import LocalVideoLoader

pytest.importorskip("cv2")
pytest.importorskip("scenedetect")
pytest.importorskip("pytesseract")

FFMPEG_AVAILABLE = (
    shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
)
TESSERACT_AVAILABLE = shutil.which("tesseract") is not None
pytestmark = pytest.mark.skipif(
    not (FFMPEG_AVAILABLE and TESSERACT_AVAILABLE),
    reason="ffmpeg/ffprobe/tesseract not on PATH",
)

_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


@pytest.fixture
def video_with_text_in_two_scenes(tmp_path: Path) -> Path:
    """Real video: black 'EXIT' on white 2s, white 'POLICE' on black 2s."""
    path = tmp_path / "text_scenes.mp4"
    drawtext = (
        "drawtext=fontfile={font}:fontcolor={color}:fontsize=40:"
        "x=(w-text_w)/2:y=(h-text_h)/2"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=white:duration=2:size=320x120:rate=10",
            "-f",
            "lavfi",
            "-i",
            "color=c=black:duration=2:size=320x120:rate=10",
            "-filter_complex",
            f"[0:v]{drawtext.format(font=_FONT, color='black')}:text='EXIT'[v0];"
            f"[1:v]{drawtext.format(font=_FONT, color='white')}:text='POLICE'[v1];"
            "[v0][v1]concat=n=2:v=1:a=0",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        capture_output=True,
        check=True,
        timeout=30,
    )
    return path


def test_real_text_correctly_attributed_per_scene(
    video_with_text_in_two_scenes: Path, tmp_path: Path
):
    video_media = LocalVideoLoader(video_with_text_in_two_scenes).load()
    enricher = FFprobeEnricher()

    frame_provider = FFmpegFrameExtractionProvider(
        frame_count=6, output_dir=tmp_path / "frames"
    )
    frame_result = Pipeline(provider=frame_provider, enricher=enricher).run_detailed(
        video_media
    )
    scene_result = Pipeline(
        provider=PySceneDetectProvider(), enricher=enricher
    ).run_detailed(video_media)

    assert len(scene_result.artifacts) == 2  # sanity: real cuts found

    ocr_pipeline = Pipeline(provider=TesseractOCRProvider())
    ocr_artifacts = []
    for frame_artifact in frame_result.artifacts:
        frame_media = LocalImageLoader(frame_artifact.frame_path).load()
        ocr_artifacts.extend(ocr_pipeline.run(frame_media))

    all_artifacts = [*frame_result.artifacts, *scene_result.artifacts, *ocr_artifacts]
    entities = SceneTextBuilder().build(all_artifacts)

    assert len(entities) == 2
    scene0, scene1 = sorted(entities, key=lambda e: e.metadata["scene_index"])

    # The actual proof: real burned-in text, correctly OCR'd, correctly
    # attributed to the scene it actually appears in -- not the other one.
    assert scene0.payload is not None and "EXIT" in scene0.payload
    assert scene1.payload is not None and "POLICE" in scene1.payload
    assert "POLICE" not in (scene0.payload or "")
    assert "EXIT" not in (scene1.payload or "")
