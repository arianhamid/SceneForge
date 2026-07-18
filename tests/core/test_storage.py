"""Tests for the ArtifactStore / content-addressable persistence layer."""

from sceneforge.core.artifact import Artifact, ArtifactKind
from sceneforge.core.identity_artifact import IdentityArtifact
from sceneforge.core.storage import (
    FileArtifactStore,
    InMemoryArtifactStore,
    artifact_from_dict,
    artifact_to_dict,
    content_key,
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


def test_content_key_changes_with_media_identity():
    key1 = content_key(_image(), "captioner", "1.0.0")
    key2 = content_key(_image(), "captioner", "1.0.0")
    # Different ImageMedia instances get different ids by default.
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
