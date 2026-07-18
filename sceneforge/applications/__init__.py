"""
SceneForge Applications Layer

High-level, user-facing applications built on top of the framework's
knowledge layer. Each application accepts an EntityStore, collects
structured data, and renders it in a consumable format.
"""

from sceneforge.applications.scene_summary import SceneSummary, SceneSummaryData

__all__ = ["SceneSummary", "SceneSummaryData"]
