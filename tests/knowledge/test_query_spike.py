"""
Sprint 7 spike: does querying EntityStore need an index or a real
backend, or is "enumerate everything, filter in memory" good enough?

Answered with a synthetic dataset sized like a real, if modest, movie
library -- not the three-scene fixtures earlier tests use -- against
the real FileEntityStore (actual disk I/O), and an actual wall-clock
measurement, not a guess. See docs/adr/0014-relationship-query-spike.md
for the numbers this test produced and what they mean.
"""

from __future__ import annotations

import time
from uuid import uuid4

import pytest

from sceneforge.knowledge.entity import Entity, EntityKind
from sceneforge.knowledge.relationship_builder import SceneSequenceBuilder
from sceneforge.knowledge.storage import (
    FileEntityStore,
    find_related,
    iter_all_entities,
)

# Sized to resemble a modest real library: a few hundred movies, a
# realistic scene count per movie -- not the three-scene toy fixtures
# used elsewhere. Big enough that an O(n) scan would show it if it
# were actually going to be a problem at any near-term real scale.
MOVIE_COUNT = 300
SCENES_PER_MOVIE = 20


@pytest.fixture(scope="module")
def populated_store(tmp_path_factory):
    root = tmp_path_factory.mktemp("entity_query_spike")
    store = FileEntityStore(root)

    target_scene_id = None
    for movie_index in range(MOVIE_COUNT):
        media_id = str(uuid4())
        scenes = [
            Entity(
                kind=EntityKind.SCENE,
                builder="scene_grouping",
                metadata={"media_id": media_id, "scene_index": i},
            )
            for i in range(SCENES_PER_MOVIE)
        ]
        if movie_index == MOVIE_COUNT // 2:
            # Pick one real scene, buried in the middle of the
            # dataset, to search for later -- not the first or last
            # record, which could hide an accidentally-linear-only
            # lucky case.
            target_scene_id = scenes[3].id

        relationships = SceneSequenceBuilder().relate(scenes)

        store.put(f"scenes:{media_id}", scenes)
        store.put(f"relationships:{media_id}", relationships)

    assert target_scene_id is not None
    return store, target_scene_id


def test_dataset_is_actually_at_realistic_scale(populated_store):
    store, _ = populated_store
    total_keys = len(store.keys())
    # one scenes key + one relationships key per movie
    assert total_keys == MOVIE_COUNT * 2


def test_find_related_returns_correct_results_at_scale(populated_store):
    store, target_scene_id = populated_store

    related = find_related(store, target_scene_id)

    # Scene index 3 (0-indexed) in a 20-scene movie has exactly two
    # relationships: (2 precedes 3) and (3 precedes 4).
    assert len(related) == 2
    assert all(e.kind == EntityKind.RELATIONSHIP for e in related)


def test_find_related_completes_in_reasonable_time_at_scale(populated_store):
    store, target_scene_id = populated_store

    start = time.monotonic()
    find_related(store, target_scene_id)
    elapsed = time.monotonic() - start

    total_entities = MOVIE_COUNT * (SCENES_PER_MOVIE + (SCENES_PER_MOVIE - 1))
    print(
        f"\nfind_related() over {total_entities} entities "
        f"({len(store.keys())} store keys): {elapsed:.3f}s"
    )

    # Generous bound -- this isn't a strict perf gate, it's evidence
    # for the ADR-0014 conclusion. If this ever gets slow enough to
    # threaten this bound, that's itself a signal Sprint 7's answer
    # needs revisiting, not a reason to raise the bound quietly.
    assert elapsed < 5.0


def test_iter_all_entities_yields_expected_total(populated_store):
    store, _ = populated_store

    total = sum(1 for _ in iter_all_entities(store))
    expected = MOVIE_COUNT * (SCENES_PER_MOVIE + (SCENES_PER_MOVIE - 1))
    assert total == expected
