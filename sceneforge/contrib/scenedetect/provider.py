"""
SceneForge PySceneDetect Provider

Real implementation of `Capability.DETECT_SCENES`, using the
`scenedetect` library's content-aware cut detection. No model weights,
no network access -- pure frame-difference analysis -- which makes
this the framework's first real capability that's genuinely trivial to
integration-test in any environment (see
`tests/contrib/test_scenedetect_integration.py`).
"""

from __future__ import annotations

from typing import Any

from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact
from sceneforge.core.artifact import Artifact
from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import ProviderError
from sceneforge.core.provider import Provider
from sceneforge.media.base import Media
from sceneforge.media.video import VideoMedia

DEFAULT_THRESHOLD = 27.0
DEFAULT_MIN_SCENE_LEN = 15  # scenedetect's own default: ~0.5-1.5s depending on fps


class PySceneDetectProvider(Provider):
    """
    Detects scene (shot) boundaries in a video via content-aware cut
    detection (`scenedetect.ContentDetector`).

    ``threshold`` controls sensitivity -- scenedetect's own default
    (27.0) is a reasonable starting point; lower values detect more
    (softer) cuts, higher values only the sharpest ones. Tune per
    content type rather than assuming one value fits all footage.

    ``min_scene_len`` (in frames) filters out cuts closer together than
    this -- scenedetect's own default is 15 frames, which at a typical
    24-30fps means anything shorter than roughly half a second to a
    second is merged into its neighbor. Content with genuinely rapid
    cuts (action sequences, montages) may need this lowered; the
    default is tuned for typical narrative pacing, not every genre.
    """

    def __init__(
        self,
        threshold: float = DEFAULT_THRESHOLD,
        min_scene_len: int = DEFAULT_MIN_SCENE_LEN,
    ) -> None:
        self._threshold = threshold
        self._min_scene_len = min_scene_len

    @property
    def name(self) -> str:
        return "pyscenedetect"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.DETECT_SCENES})

    def run(self, media: Media) -> list[Artifact[Any]]:
        if not isinstance(media, VideoMedia):
            raise TypeError(f"Expected VideoMedia, got {type(media).__name__}")

        source = media.metadata.get("source")
        if not source:
            raise ProviderError(
                "VideoMedia has no 'source' path in metadata -- load it via "
                "LocalVideoLoader (or set metadata['source'] yourself) before "
                "detecting scenes."
            )

        try:
            from scenedetect import ContentDetector, detect
        except ImportError as exc:
            raise ProviderError(
                "The 'scenedetect' package is required for PySceneDetectProvider "
                "(pip install scenedetect)."
            ) from exc

        try:
            scenes = detect(
                str(source),
                ContentDetector(
                    threshold=self._threshold, min_scene_len=self._min_scene_len
                ),
            )
        except Exception as exc:  # noqa: BLE001 - re-branded, not swallowed
            raise ProviderError(
                f"scene detection failed for '{source}': {exc}"
            ) from exc

        if not scenes:
            # No cuts detected -- treat the whole video as one scene,
            # matching scenedetect's own `start_in_scene` convention,
            # rather than silently returning nothing.
            duration = media.duration if media.duration > 0 else 0.0
            return [
                SceneCutArtifact(
                    media_id=media.id,
                    provider=self.name,
                    scene_index=0,
                    start_seconds=0.0,
                    end_seconds=duration,
                    start_frame=0,
                    end_frame=0,
                )
            ]

        artifacts: list[Artifact[Any]] = []
        for index, (start, end) in enumerate(scenes):
            artifacts.append(
                SceneCutArtifact(
                    media_id=media.id,
                    provider=self.name,
                    scene_index=index,
                    start_seconds=start.seconds,
                    end_seconds=end.seconds,
                    start_frame=start.frame_num,
                    end_frame=end.frame_num,
                )
            )
        return artifacts
