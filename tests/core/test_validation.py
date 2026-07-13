import pytest

from sceneforge.core.capability import Capability
from sceneforge.core.exceptions import InvalidMetadataError
from sceneforge.core.provider_metadata import ProviderMetadata
from sceneforge.core.validation import validate_provider_metadata


def test_valid_metadata():
    metadata = ProviderMetadata(
        name="test",
        version="1.0.0",
        description="Test provider",
        capabilities=frozenset({Capability.CAPTION}),
    )
    validate_provider_metadata(metadata)


def test_empty_name():
    metadata = ProviderMetadata(
        name="",
        version="1.0.0",
        description="Test provider",
        capabilities=frozenset({Capability.CAPTION}),
    )
    with pytest.raises(InvalidMetadataError) as exc_info:
        validate_provider_metadata(metadata)
    assert exc_info.value.field == "name"


def test_empty_version():
    metadata = ProviderMetadata(
        name="test",
        version="",
        description="Test provider",
        capabilities=frozenset({Capability.CAPTION}),
    )
    with pytest.raises(InvalidMetadataError) as exc_info:
        validate_provider_metadata(metadata)
    assert exc_info.value.field == "version"
