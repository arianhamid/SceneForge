"""
Sprint 11 spike: does a genuinely cross-video query (aggregating
across an entire library, not looking up one known entity within it)
need anything beyond iter_all_entities() as it exists today?

Deliberately a different shape of question from ADR-0014's spike:
find_related() searches for everything connected to one already-known
entity id -- a targeted lookup. This test performs a full-library
aggregation (rank every movie by total face count) that has no
shortcut: every entity in the store must be read and considered. If
iter_all_entities() is going to show a real limit, an unavoidable
full-scan aggregation is where it would show up.

See docs/adr/0019-cross-video-query-spike.md for the measurement this
test produced and what it means.
"""

from __future__ import annotations

import time
from uuid import uuid4

import pytest

from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.relationship_builder import SceneSequenceBuilder
from sceneforge.knowledge.scene_merge_builder import SceneMergeBuilder
from sceneforge.knowledge.storage import FileEntityStore, iter_all_entities

# Sized like a genuinely multi-video library -- 400 movies is well
# beyond anything this project has actually processed (one video at a
# time, by hand, in every prior sprint's real integration tests).
MOVIE_COUNT = 400
SCENES_PER_MOVIE = 15


@pytest.fixture(scope="module")
def library_store(tmp_path_factory):
    """
    A realistic multi-stage library: for each movie, both
    SceneGroupingBuilder-shaped and SceneFaceBuilder-shaped entities,
    merged via SceneMergeBuilder -- the full Sprint 8-10 pipeline
    output, replicated across many movies, not just one.
    """
    root = tmp_path_factory.mktemp("cross_video_query_spike")
    store = FileEntityStore(root)

    for movie_index in range(MOVIE_COUNT):
        media_id = str(uuid4())
        # A deterministic-but-varied face count per movie so the
        # aggregation query below has real, checkable structure.
        faces_per_scene = movie_index % 5  # 0..4 faces per scene

        dialogue_entities = [
            Entity(
                kind=EntityKind.SCENE,
                builder="scene_grouping",
                payload=f"line for scene {i}" if i % 3 == 0 else None,
                metadata={
                    "media_id": media_id,
                    "scene_index": i,
                    "start_seconds": float(i),
                    "end_seconds": float(i + 1),
                },
            )
            for i in range(SCENES_PER_MOVIE)
        ]
        face_entities = [
            Entity(
                kind=EntityKind.SCENE,
                builder="scene_face",
                payload=faces_per_scene,
                metadata={
                    "media_id": media_id,
                    "scene_index": i,
                    "start_seconds": float(i),
                    "end_seconds": float(i + 1),
                    "total_faces": faces_per_scene,
                },
            )
            for i in range(SCENES_PER_MOVIE)
        ]
        merged = SceneMergeBuilder().relate([*dialogue_entities, *face_entities])
        sequence = SceneSequenceBuilder().relate(dialogue_entities)

        store.put(f"dialogue:{media_id}", dialogue_entities)
        store.put(f"faces:{media_id}", face_entities)
        store.put(f"merged:{media_id}", merged)
        store.put(f"sequence:{media_id}", sequence)

    return store, faces_per_scene  # last movie's rate, used by one test below


def test_library_is_at_realistic_multi_video_scale(library_store):
    store, _ = library_store
    # 4 keys per movie (dialogue, faces, merged, sequence).
    assert len(store.keys()) == MOVIE_COUNT * 4


def test_full_library_aggregation_completes_in_reasonable_time(library_store):
    store, _ = library_store

    start = time.monotonic()
    totals_by_media: dict[str, int] = {}
    for entity in iter_all_entities(store):
        if entity.kind != EntityKind.SCENE or entity.builder != "scene_merge":
            continue
        media_id = entity.metadata["media_id"]
        faces = entity.metadata["scene_face"]["total_faces"]
        totals_by_media[media_id] = totals_by_media.get(media_id, 0) + faces
    elapsed = time.monotonic() - start

    total_entities = MOVIE_COUNT * (SCENES_PER_MOVIE * 3 + (SCENES_PER_MOVIE - 1))
    print(
        f"\nFull-library aggregation over {total_entities} entities "
        f"({len(store.keys())} store keys, {MOVIE_COUNT} movies): {elapsed:.3f}s"
    )

    assert len(totals_by_media) == MOVIE_COUNT
    # Generous bound, same discipline as ADR-0014's test: evidence for
    # this measurement, not a permanent guarantee.
    assert elapsed < 10.0


def test_aggregation_produces_correct_ranking(library_store):
    store, _ = library_store

    totals_by_media: dict[str, int] = {}
    for entity in iter_all_entities(store):
        if entity.kind != EntityKind.SCENE or entity.builder != "scene_merge":
            continue
        media_id = entity.metadata["media_id"]
        faces = entity.metadata["scene_face"]["total_faces"]
        totals_by_media[media_id] = totals_by_media.get(media_id, 0) + faces

    # Movies were seeded with faces_per_scene = movie_index % 5, so the
    # maximum possible total per movie is 4 * SCENES_PER_MOVIE.
    max_total = max(totals_by_media.values())
    assert max_total == 4 * SCENES_PER_MOVIE

    # At least one movie should have zero faces (movie_index % 5 == 0).
    assert 0 in totals_by_media.values()


def test_filtering_across_library_for_high_face_count_movies(library_store):
    store, _ = library_store
    threshold = 3 * SCENES_PER_MOVIE  # movies averaging >3 faces/scene

    totals_by_media: dict[str, int] = {}
    for entity in iter_all_entities(store):
        if entity.kind != EntityKind.SCENE or entity.builder != "scene_merge":
            continue
        media_id = entity.metadata["media_id"]
        faces = entity.metadata["scene_face"]["total_faces"]
        totals_by_media[media_id] = totals_by_media.get(media_id, 0) + faces

    matching = [m for m, total in totals_by_media.items() if total > threshold]
    # movie_index % 5 == 4 gives 4 faces/scene -> the only bucket above
    # a 3-faces/scene threshold; that's 1 in 5 movies.
    assert len(matching) == MOVIE_COUNT // 5
