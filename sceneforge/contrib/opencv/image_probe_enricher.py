"""
SceneForge OpenCV Image Enricher

`LocalImageLoader` (`sceneforge/media/image_loader.py`) has produced
placeholder `width=0, height=0` for every `ImageMedia` since Sprint 1
-- real dimensions require decoding the file, which loaders
deliberately don't do (`docs/specifications/MEDIA_SPEC.md`). Every
prior sprint fixed this for video (`FFprobeEnricher`) but never for
images. This is the same fix, for the same reason, one media type
later: read the real file with OpenCV and return a corrected
`ImageMedia` via `Media.evolve()`.
"""

from __future__ import annotations

from sceneforge.core.exceptions import EnrichmentError
from sceneforge.media.base import Media
from sceneforge.media.image import ImageMedia


class OpenCVImageEnricher:
    """
    MediaEnricher that fills in real width/height for ImageMedia by
    decoding the file referenced in `media.metadata["source"]` with
    OpenCV.

    Non-ImageMedia is returned unchanged. ImageMedia with no `source`
    in its metadata is returned unchanged -- nothing to probe.
    """

    def enrich(self, media: Media) -> Media:
        if not isinstance(media, ImageMedia):
            return media

        source = media.metadata.get("source")
        if not source:
            return media

        try:
            import cv2
        except ImportError as exc:
            raise EnrichmentError(
                "OpenCVImageEnricher",
                ImportError(
                    "opencv-python(-headless) is required "
                    "(pip install opencv-python-headless)"
                ),
            ) from exc

        image = cv2.imread(str(source))
        if image is None:
            raise EnrichmentError(
                "OpenCVImageEnricher",
                ValueError(f"OpenCV could not decode image at '{source}'"),
            )

        height, width = image.shape[:2]
        return media.evolve(width=width, height=height)
