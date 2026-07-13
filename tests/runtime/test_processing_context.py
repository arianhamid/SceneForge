import pytest

from sceneforge.core.exceptions import ProcessingCancelledError
from sceneforge.runtime import ProcessingContext


def test_context_defaults():
    context = ProcessingContext()

    assert context.request_id is None
    assert context.cancelled is False
    assert context.metadata == {}


def test_context_cancel():
    context = ProcessingContext()

    context.cancel()

    assert context.cancelled


def test_ensure_running_when_not_cancelled():
    context = ProcessingContext()
    context.ensure_running()  # Should not raise


def test_ensure_running_when_cancelled():
    context = ProcessingContext()
    context.cancel()

    with pytest.raises(ProcessingCancelledError):
        context.ensure_running()
