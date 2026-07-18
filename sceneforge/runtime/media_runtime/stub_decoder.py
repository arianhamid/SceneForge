"""
SceneForge Stub Decoder

Reference implementation of Decoder for testing.
Returns placeholder representations without actual decoding.
"""

from __future__ import annotations

from typing import Any

from sceneforge.media.audio import AudioMedia
from sceneforge.media.base import Media
from sceneforge.media.image import ImageMedia
from sceneforge.media.video import VideoMedia
from sceneforge.runtime.media_runtime.audio_representation import AudioRepresentation
from sceneforge.runtime.media_runtime.image_representation import ImageRepresentation
from sceneforge.runtime.media_runtime.video_representation import VideoRepresentation


class StubDecoder:
    """
    Stub decoder for testing.

    Returns placeholder representations without actual decoding.
    """

    def decode(self, media: Media) -> Any:
        """
        Decode media into a placeholder representation.

        Args:
            media: The media object to decode.

        Returns:
            A placeholder representation.
        """
        if isinstance(media, ImageMedia):
            return ImageRepresentation(
                media_id=media.id,
                width=media.width,
                height=media.height,
                dtype="uint8",
                shape=(media.height, media.width, 3),
                data=None,  # Stub: no actual data
            )
        elif isinstance(media, VideoMedia):
            return VideoRepresentation(
                media_id=media.id,
                duration=media.duration,
                fps=media.fps,
                frame_count=media.frame_count,
                width=640,  # Stub: default width
                height=480,  # Stub: default height
            )
        elif isinstance(media, AudioMedia):
            return AudioRepresentation(
                media_id=media.id,
                duration=media.duration,
                sample_rate=media.sample_rate,
                channels=media.channels,
                bit_depth=media.bit_depth,
            )
        else:
            raise TypeError(f"Unsupported media type: {type(media)}")
