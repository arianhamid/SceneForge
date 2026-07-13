from __future__ import annotations

import re

from sceneforge.core.exceptions import InvalidNameError

_PATTERN = re.compile(r"^[a-z0-9]+(\.[a-z0-9_]+)+$")


def validate_qualified_name(name: str) -> str:
    """
    Validate a SceneForge qualified name.

    Examples
    --------
    builtin.ffmpeg
    openai.whisper
    community.pyannote
    """

    if not _PATTERN.fullmatch(name):
        raise InvalidNameError(name)

    return name
