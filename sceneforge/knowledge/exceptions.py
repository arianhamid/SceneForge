"""SceneForge Knowledge Layer Exceptions"""

from __future__ import annotations

from sceneforge.core.exceptions import SceneForgeError


class KnowledgeBuilderError(SceneForgeError):
    """Raised when a Knowledge Builder cannot build entities from the
    given artifacts."""
