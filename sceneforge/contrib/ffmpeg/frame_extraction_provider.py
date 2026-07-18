"""
SceneForge FFmpeg Frame Extraction Provider

SceneForge's first real capability implementation: extracts N
evenly-spaced frames from a video file via `ffmpeg`, proving the
Media -> Provider -> Artifact contract end-to-end against a real
external tool instead of a stub.

Wants a VideoMedia enriched with a real `duration` (see
`FFprobeEnricher`) -- frame timestamps are an even split of the
reported duration, so an un-enriched, placeholder VideoMedia
(`duration=0.0`) would only manage a single frame at t=0. Pair this
provider with FFprobeEnricher via `Pipeline(..., enricher=...)` in
practice.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from sceneforge.contrib.ffmpeg.frame_extraction_artifact import FrameExtractionArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import ProviderError
from sceneforge.core.provider import Provider
from sceneforge.media.base import Media
from sceneforge.media.video import VideoMedia

DEFAULT_FFMPEG_BINARY = "ffmpeg"
_EXTRACT_TIMEOUT_SECONDS = 30


class FFmpegBinaryMissingError(ProviderError):
    """Raised when the configured ffmpeg binary can't be found on PATH."""

    def __init__(self, binary: str) -> None:
        super().__init__(f"'{binary}' not found on PATH")


class FFmpegFrameExtractionProvider(Provider):
    """
    Extracts ``frame_count`` evenly-spaced frames from a video via ffmpeg.

    Frames are written as PNG files under ``output_dir`` (a fresh temp
    directory per instance if not supplied) and referenced by path in
    each artifact -- SceneForge artifacts carry observations, not raw
    pixel buffers, so the pixels live on disk and the Artifact just
    points at them.
    """

    def __init__(
        self,
        frame_count: int = 5,
        output_dir: str | Path | None = None,
        ffmpeg_binary: str = DEFAULT_FFMPEG_BINARY,
    ) -> None:
        if frame_count < 1:
            raise ValueError("frame_count must be >= 1")
        self._frame_count = frame_count
        self._output_dir = Path(output_dir) if output_dir else None
        self._ffmpeg_binary = ffmpeg_binary

    @property
    def name(self) -> str:
        return "ffmpeg_frame_extraction"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.FRAME_EXTRACTION})

    def run(self, media: Media) -> list[Artifact[Any]]:
        if not isinstance(media, VideoMedia):
            raise TypeError(f"Expected VideoMedia, got {type(media).__name__}")

        source = media.metadata.get("source")
        if not source:
            raise ProviderError(
                "VideoMedia has no 'source' path in metadata -- load it via "
                "LocalVideoLoader (or set metadata['source'] yourself) before "
                "extracting frames."
            )

        if shutil.which(self._ffmpeg_binary) is None:
            raise FFmpegBinaryMissingError(self._ffmpeg_binary)

        output_dir = self._output_dir or Path(
            tempfile.mkdtemp(prefix="sceneforge_frames_")
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        duration = media.duration if media.duration > 0 else 1.0
        timestamps = self._evenly_spaced_timestamps(duration, self._frame_count)

        artifacts: list[Artifact[Any]] = []
        for index, timestamp in enumerate(timestamps):
            frame_path = output_dir / f"{media.id}_frame_{index:04d}.png"
            self._extract_frame(str(source), timestamp, frame_path)
            artifacts.append(
                FrameExtractionArtifact(
                    media_id=media.id,
                    provider=self.name,
                    frame_path=str(frame_path),
                    timestamp_seconds=timestamp,
                    frame_index=index,
                )
            )
        return artifacts

    @staticmethod
    def _evenly_spaced_timestamps(duration: float, count: int) -> list[float]:
        if count == 1:
            return [round(duration / 2, 3)]
        step = duration / count
        return [round(step * i + step / 2, 3) for i in range(count)]

    def _extract_frame(self, source: str, timestamp: float, output_path: Path) -> None:
        command = [
            self._ffmpeg_binary,
            "-y",
            "-ss",
            f"{timestamp:.3f}",
            "-i",
            source,
            "-frames:v",
            "1",
            "-q:v",
            "2",
            str(output_path),
        ]
        try:
            subprocess.run(
                command,
                capture_output=True,
                check=True,
                timeout=_EXTRACT_TIMEOUT_SECONDS,
            )
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            OSError,
        ) as exc:
            raise ProviderError(
                f"ffmpeg frame extraction failed at t={timestamp}: {exc}"
            ) from exc
