"""
SceneForge Media Enrichment

Loaders are deliberately cheap: they touch the filesystem, not the
codec, so ``LocalVideoLoader`` hands back a ``VideoMedia`` with
``fps=0.0`` and ``codec="unknown"``. Something has to turn that into
real numbers before capability validation or a Provider can trust it
-- that "something" is a MediaEnricher.

An Enricher never mutates the Media it receives (Media is frozen).
It returns a *new* instance built through ``Media.evolve()``, and the
Pipeline is responsible for threading that new instance forward.

This deliberately sits *outside* Provider: enrichment corrects the
Media object itself, while a Provider observes a (possibly already
enriched) Media object and produces Artifacts about it. Conflating
the two would mean every caption/OCR/transcription provider also had
to know how to probe a video file.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from sceneforge.media.base import Media


@runtime_checkable
class MediaEnricher(Protocol):
    """
    Protocol for turning placeholder Media into authoritative Media.

    Any class with an ``enrich()`` method matching this signature
    participates -- implementations don't need to inherit from this
    protocol.
    """

    def enrich(self, media: Media) -> Media:
        """
        Inspect ``media`` and return a new, fully-populated instance.

        Implementations must not mutate ``media`` in place. If nothing
        needs correcting, they may return ``media`` unchanged.
        """
        ...


class ChainedEnricher:
    """
    Runs a sequence of enrichers in order, threading the result of
    each into the next.

    Useful when several independent enrichers each know how to fill
    in a different slice of metadata (e.g. an ffprobe enricher for
    technical fields, a perceptual-hash enricher for a dedup key).
    """

    def __init__(self, enrichers: list[MediaEnricher]) -> None:
        self._enrichers = list(enrichers)

    def enrich(self, media: Media) -> Media:
        for enricher in self._enrichers:
            media = enricher.enrich(media)
        return media
