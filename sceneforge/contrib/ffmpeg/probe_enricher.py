"""
SceneForge FFprobe Enricher

SceneForge's reference MediaEnricher: turns the placeholder VideoMedia
produced by LocalVideoLoader (`duration=0.0`, `codec="unknown"`,
`fps=0.0`) into authoritative values by shelling out to `ffprobe`.

This is the concrete answer to the "how does enrichment actually get
authoritative metadata onto an immutable Media object" question that
was previously left open: LocalVideoLoader stashes the source path in
`metadata["source"]`, and this enricher reads it, probes the real
file, and returns a new VideoMedia via `Media.evolve()`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any

from sceneforge.core.exceptions import EnrichmentError
from sceneforge.media.base import Media
from sceneforge.media.video import VideoMedia

DEFAULT_FFPROBE_BINARY = "ffprobe"
_PROBE_TIMEOUT_SECONDS = 30


class FFprobeMissingError(EnrichmentError):
    """Raised when the configured ffprobe binary can't be found on PATH."""

    def __init__(self, binary: str) -> None:
        super().__init__(
            "FFprobeEnricher", FileNotFoundError(f"'{binary}' not found on PATH")
        )


class FFprobeEnricher:
    """
    MediaEnricher that fills in real duration/codec/fps for VideoMedia
    by probing the file referenced in ``media.metadata["source"]``.

    Media types other than VideoMedia, or VideoMedia with no
    ``source`` in its metadata, are returned unchanged -- this
    enricher only corrects what it actually knows how to probe rather
    than guessing.
    """

    def __init__(self, ffprobe_binary: str = DEFAULT_FFPROBE_BINARY) -> None:
        self._ffprobe_binary = ffprobe_binary

    def enrich(self, media: Media) -> Media:
        if not isinstance(media, VideoMedia):
            return media

        source = media.metadata.get("source")
        if not source:
            return media

        if shutil.which(self._ffprobe_binary) is None:
            raise FFprobeMissingError(self._ffprobe_binary)

        probed = self._probe(str(source))
        return media.evolve(
            duration=probed["duration"],
            codec=probed["codec"],
            fps=probed["fps"],
            metadata={
                "width": probed["width"],
                "height": probed["height"],
                "probed": True,
            },
        )

    def _probe(self, source: str) -> dict[str, Any]:
        command = [
            self._ffprobe_binary,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            "-select_streams",
            "v:0",
            source,
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                timeout=_PROBE_TIMEOUT_SECONDS,
            )
        except (
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            OSError,
        ) as exc:
            raise EnrichmentError("FFprobeEnricher", exc) from exc

        try:
            data = json.loads(result.stdout)
            stream = data["streams"][0]
            fmt = data.get("format", {})

            num_str, _, den_str = str(stream.get("r_frame_rate", "0/1")).partition("/")
            num, den = float(num_str or 0), float(den_str or 1)
            fps = num / den if den else 0.0

            duration = float(fmt.get("duration") or stream.get("duration") or 0.0)

            return {
                "duration": duration,
                "codec": stream.get("codec_name", "unknown"),
                "fps": fps,
                "width": int(stream.get("width", 0)),
                "height": int(stream.get("height", 0)),
            }
        except (KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
            raise EnrichmentError("FFprobeEnricher", exc) from exc
