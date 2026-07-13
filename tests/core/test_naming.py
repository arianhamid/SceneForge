import pytest

from sceneforge.core.exceptions import InvalidNameError
from sceneforge.core.naming import validate_qualified_name


def test_valid_names():
    assert validate_qualified_name("builtin.ffmpeg") == "builtin.ffmpeg"
    assert validate_qualified_name("openai.whisper") == "openai.whisper"
    assert validate_qualified_name("community.pyannote") == "community.pyannote"
    assert validate_qualified_name("a.b") == "a.b"
    assert validate_qualified_name("abc.def_123") == "abc.def_123"


def test_invalid_names():
    with pytest.raises(InvalidNameError):
        validate_qualified_name("")
    
    with pytest.raises(InvalidNameError):
        validate_qualified_name("invalid")
    
    with pytest.raises(InvalidNameError):
        validate_qualified_name("Invalid.Name")
    
    with pytest.raises(InvalidNameError):
        validate_qualified_name("invalid name")
    
    with pytest.raises(InvalidNameError):
        validate_qualified_name("invalid/name")