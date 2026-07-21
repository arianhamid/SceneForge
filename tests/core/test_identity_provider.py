from sceneforge.contrib.identity.provider import IdentityProvider
from sceneforge.core.identity_artifact import IdentityArtifact
from sceneforge.media.image import ImageMedia


def test_identity_provider_returns_list():
    provider = IdentityProvider()
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")

    result = provider.run(media)

    assert isinstance(result, list)
    assert len(result) == 1


def test_identity_provider_returns_identity_artifact():
    provider = IdentityProvider()
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")

    result = provider.run(media)

    assert isinstance(result[0], IdentityArtifact)


def test_identity_provider_preserves_media_id():
    provider = IdentityProvider()
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")

    result = provider.run(media)

    assert result[0].media_id == media.id


def test_identity_provider_sets_provider_name():
    provider = IdentityProvider()
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")

    result = provider.run(media)

    assert result[0].provider == "identity"


def test_identity_provider_is_pure():
    provider = IdentityProvider()
    media = ImageMedia(name="test.jpg", width=100, height=100, fmt="JPEG")

    result1 = provider.run(media)
    result2 = provider.run(media)

    # Same input produces same content (media_id, provider name)
    assert result1[0].media_id == result2[0].media_id
    assert result1[0].provider == result2[0].provider
    assert result1[0].kind == result2[0].kind


def test_identity_provider_satisfies_protocol():
    from sceneforge.core.provider_protocol import Provider

    provider = IdentityProvider()

    assert isinstance(provider, Provider)
