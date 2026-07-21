"""
SceneForge Knowledge Layer (Layer 4: Knowledge Builders)

The first layer above Artifacts. Turns single-provider observations
into Entities -- concepts synthesized across possibly many artifacts.
See docs/architecture/LAYERS.md's Layer 4 and
docs/architecture/DOMAIN_MODEL.md's "Entity" section.

`SceneGroupingBuilder` is the first real (non-speculative)
implementation. `SceneFaceBuilder` is the first to synthesize across
two capability domains at once (video/scene structure and image/face
detection) -- see docs/adr/0016-cross-domain-knowledge-builder.md.
`SceneMergeBuilder` combines multiple builders' output for the same
scene into one entity, using the existing `RelationshipBuilder` shape
rather than a new persistence concept -- see
docs/adr/0018-scene-merge-builder.md. `SceneTextBuilder` confirms the
same cross-domain correlation pattern (source_frame_path matching)
holds for a second real capability (OCR) -- see
docs/adr/0022-real-ocr-provider.md.
"""

from sceneforge.knowledge.builder import KnowledgeBuilder, build_with_cache
from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.exceptions import KnowledgeBuilderError
from sceneforge.knowledge.relationship_builder import (
    RelationshipBuilder,
    SceneSequenceBuilder,
)
from sceneforge.knowledge.scene_face_builder import SceneFaceBuilder
from sceneforge.knowledge.scene_grouping_builder import SceneGroupingBuilder
from sceneforge.knowledge.scene_merge_builder import SceneMergeBuilder
from sceneforge.knowledge.scene_text_builder import SceneTextBuilder
from sceneforge.knowledge.storage import (
    EntityStore,
    FileEntityStore,
    InMemoryEntityStore,
    entity_build_key,
    find_related,
    iter_all_entities,
    register_entity_type,
)

__all__ = [
    "Entity",
    "EntityKind",
    "EntityStore",
    "FileEntityStore",
    "InMemoryEntityStore",
    "KnowledgeBuilder",
    "KnowledgeBuilderError",
    "RelationshipBuilder",
    "SceneFaceBuilder",
    "SceneGroupingBuilder",
    "SceneMergeBuilder",
    "SceneSequenceBuilder",
    "SceneTextBuilder",
    "build_with_cache",
    "entity_build_key",
    "find_related",
    "iter_all_entities",
    "register_entity_type",
]
