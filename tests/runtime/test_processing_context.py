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
