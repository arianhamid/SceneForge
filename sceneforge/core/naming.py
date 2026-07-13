from __future__ import annotations

import re

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
        raise ValueError(f"Invalid qualified name: {name!r}")

    return name
