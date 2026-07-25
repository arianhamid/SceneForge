"""Tests for the ArtifactStore / content-addressable persistence layer."""

from uuid import uuid4

from sceneforge.contrib.scenedetect.scene_cut_artifact import SceneCutArtifact
from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.identity_artifact import IdentityArtifact
from sceneforge.core.storage import (
    FileArtifactStore,
    InMemoryArtifactStore,
    artifact_from_dict,
    artifact_to_dict,
    content_key,
    find_artifact_by_id,
    find_artifacts_by_media,
    iter_all_artifacts,
    register_artifact_type,
)
from sceneforge.media.image import ImageMedia


def _image():
    return ImageMedia(name="frame.png", width=10, height=10, fmt="PNG")


def test_content_key_stable_for_same_inputs():
    media = _image()
    key1 = content_key(media, "captioner", "1.0.0")
    key2 = content_key(media, "captioner", "1.0.0")
    assert key1 == key2


def test_content_key_changes_with_provider_version():
    media = _image()
    key1 = content_key(media, "captioner", "1.0.0")
    key2 = content_key(media, "captioner", "2.0.0")
    assert key1 != key2


def test_content_key_stable_across_reloads_of_the_same_file(tmp_path):
    """The exact bug the 2026-07-22 implementation review reproduced live:
    `content_key()` used to derive from the random per-load `Media.id`, so
    reloading the same unchanged file was a guaranteed cache miss."""
    path = tmp_path / "frame.png"
    path.write_bytes(b"same pixel bytes")

    media_load_one = ImageMedia(name="frame.png", width=10, height=10, fmt="PNG")
    media_load_one = media_load_one.evolve(metadata={"source": str(path)})
    media_load_two = ImageMedia(name="frame.png", width=10, height=10, fmt="PNG")
    media_load_two = media_load_two.evolve(metadata={"source": str(path)})

    assert media_load_one.id != media_load_two.id  # different loads, different ids
    key1 = content_key(media_load_one, "captioner", "1.0.0")
    key2 = content_key(media_load_two, "captioner", "1.0.0")
    assert key1 == key2  # same bytes -> same key regardless


def test_content_key_changes_when_file_content_changes(tmp_path):
    path_a = tmp_path / "a.png"
    path_a.write_bytes(b"pixels a")
    path_b = tmp_path / "b.png"
    path_b.write_bytes(b"pixels b")

    media_a = ImageMedia(name="frame.png", width=10, height=10, fmt="PNG").evolve(
        metadata={"source": str(path_a)}
    )
    media_b = ImageMedia(name="frame.png", width=10, height=10, fmt="PNG").evolve(
        metadata={"source": str(path_b)}
    )

    key_a = content_key(media_a, "captioner", "1.0.0")
    key_b = content_key(media_b, "captioner", "1.0.0")
    assert key_a != key_b


def test_content_key_uses_name_fallback_for_media_with_no_backing_file():
    """Documented, deliberate limitation of the name-based fallback (see
    `media_content_identity()`'s docstring): synthetic/in-memory media with
    no `source` path collide on name alone. Real files never hit this path."""
    key1 = content_key(_image(), "captioner", "1.0.0")
    key2 = content_key(_image(), "captioner", "1.0.0")
    assert key1 == key2

    differently_named = ImageMedia(name="other.png", width=10, height=10, fmt="PNG")
    key3 = content_key(differently_named, "captioner", "1.0.0")
    assert key1 != key3


def test_content_key_changes_with_execution_fingerprint():
    media = _image()
    key1 = content_key(media, "captioner", "1.0.0", execution_fingerprint="lang=en")
    key2 = content_key(media, "captioner", "1.0.0", execution_fingerprint="lang=fr")
    assert key1 != key2


def test_artifact_round_trips_through_dict():
    artifact = Artifact(
        kind=ArtifactKind.CAPTION, provider="captioner", payload="a cat"
    )
    as_dict = artifact_to_dict(artifact)
    restored = artifact_from_dict(as_dict)

    assert restored.id == artifact.id
    assert restored.kind == artifact.kind
    assert restored.provider == artifact.provider
    assert restored.payload == artifact.payload


def test_identity_artifact_round_trips_with_subclass_fields():
    media = _image()
    artifact = IdentityArtifact(media_id=media.id, provider="identity")
    restored = artifact_from_dict(artifact_to_dict(artifact))

    assert isinstance(restored, IdentityArtifact)
    assert restored.media_id == media.id


def test_file_store_put_get_roundtrip(tmp_path):
    store = FileArtifactStore(tmp_path)
    media = _image()
    key = content_key(media, "captioner", "1.0.0")
    artifacts = [
        Artifact(kind=ArtifactKind.CAPTION, provider="captioner", payload="a cat")
    ]

    assert store.get(key) is None
    assert not store.has(key)

    store.put(key, artifacts)

    assert store.has(key)
    cached = store.get(key)
    assert cached is not None
    assert cached[0].payload == "a cat"


def test_file_store_persists_across_instances(tmp_path):
    media = _image()
    key = content_key(media, "captioner", "1.0.0")
    artifacts = [
        Artifact(kind=ArtifactKind.CAPTION, provider="captioner", payload="a cat")
    ]

    FileArtifactStore(tmp_path).put(key, artifacts)

    # A brand new store instance pointed at the same root should see it --
    # this is what makes "analyze once, reuse forever" survive a restart.
    reopened = FileArtifactStore(tmp_path)
    cached = reopened.get(key)
    assert cached is not None
    assert cached[0].payload == "a cat"


def test_file_store_delete(tmp_path):
    store = FileArtifactStore(tmp_path)
    key = "some-key"
    store.put(key, [Artifact(provider="x")])
    assert store.has(key)

    store.delete(key)
    assert not store.has(key)
    # Deleting an already-missing key is a no-op, not an error.
    store.delete(key)


def test_in_memory_store_roundtrip():
    store = InMemoryArtifactStore()
    key = "k"
    store.put(key, [Artifact(kind=ArtifactKind.OCR, provider="ocr", payload="hi")])

    cached = store.get(key)
    assert cached is not None
    assert cached[0].payload == "hi"
    assert store.has(key)

    store.delete(key)
    assert store.get(key) is None


def test_register_artifact_type_enables_exact_roundtrip():
    from dataclasses import dataclass

    @register_artifact_type
    @dataclass(frozen=True, slots=True)
    class NoteArtifact(Artifact[str]):
        language: str = "en"

    artifact = NoteArtifact(provider="notes", payload="hello", language="fa")
    restored = artifact_from_dict(artifact_to_dict(artifact))

    assert isinstance(restored, NoteArtifact)
    assert restored.language == "fa"


def _scene_cut(media_id, index=0, start=0.0, end=2.0):
    return SceneCutArtifact(
        media_id=media_id, scene_index=index, start_seconds=start, end_seconds=end
    )


def test_file_artifact_store_keys_lists_every_stored_key(tmp_path):
    store = FileArtifactStore(tmp_path)
    store.put("k1", [_scene_cut(uuid4())])
    store.put("k2", [_scene_cut(uuid4())])

    assert sorted(store.keys()) == ["k1", "k2"]


def test_in_memory_artifact_store_keys_lists_every_stored_key():
    store = InMemoryArtifactStore()
    store.put("k1", [_scene_cut(uuid4())])
    store.put("k2", [_scene_cut(uuid4())])

    assert sorted(store.keys()) == ["k1", "k2"]


def test_iter_all_artifacts_flattens_every_key(tmp_path):
    store = FileArtifactStore(tmp_path)
    media_id = uuid4()
    store.put("k1", [_scene_cut(media_id, index=0)])
    store.put("k2", [_scene_cut(media_id, index=1)])

    scene_indices = sorted(a.scene_index for a in iter_all_artifacts(store))
    assert scene_indices == [0, 1]


def test_find_artifact_by_id_returns_the_matching_artifact():
    store = InMemoryArtifactStore()
    target = _scene_cut(uuid4())
    other = _scene_cut(uuid4())
    store.put("k1", [target, other])

    found = find_artifact_by_id(store, target.id)

    assert found is not None
    assert found.id == target.id


def test_find_artifact_by_id_returns_none_when_absent():
    store = InMemoryArtifactStore()
    store.put("k1", [_scene_cut(uuid4())])

    assert find_artifact_by_id(store, uuid4()) is None


def test_find_artifacts_by_media_filters_to_the_requested_media():
    store = InMemoryArtifactStore()
    media_a = uuid4()
    media_b = uuid4()
    store.put("k1", [_scene_cut(media_a, index=0), _scene_cut(media_b, index=0)])
    store.put("k2", [_scene_cut(media_a, index=1)])

    found = find_artifacts_by_media(store, media_a)

    assert {a.scene_index for a in found} == {0, 1}
    assert all(a.media_id == media_a for a in found)


def test_find_artifacts_by_media_excludes_artifacts_with_no_media_id():
    from dataclasses import dataclass

    @dataclass(frozen=True, slots=True)
    class NoMediaArtifact(Artifact[str]):
        pass

    store = InMemoryArtifactStore()
    store.put("k1", [NoMediaArtifact(provider="x", payload="hash")])

    assert find_artifacts_by_media(store, uuid4()) == []
