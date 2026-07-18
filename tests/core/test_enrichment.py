"""Tests for MediaEnricher / ChainedEnricher."""

from sceneforge.core.enrichment import ChainedEnricher
from sceneforge.media.video import VideoMedia


class FpsEnricher:
    def enrich(self, media):
        return media.evolve(fps=24.0)


class CodecEnricher:
    def enrich(self, media):
        return media.evolve(codec="h264")


def _video():
    return VideoMedia(name="movie.mp4", duration=0.0, codec="unknown", fps=0.0)


def test_single_enricher():
    result = FpsEnricher().enrich(_video())
    assert result.fps == 24.0
    assert result.codec == "unknown"


def test_chained_enricher_applies_all_in_order():
    chained = ChainedEnricher([FpsEnricher(), CodecEnricher()])
    result = chained.enrich(_video())

    assert result.fps == 24.0
    assert result.codec == "h264"


def test_chained_enricher_empty_list_is_identity():
    chained = ChainedEnricher([])
    original = _video()
    result = chained.enrich(original)

    assert result == original
