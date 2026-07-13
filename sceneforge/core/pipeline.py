from __future__ import annotations

from collections.abc import Iterable

from sceneforge.core.artifact import Artifact
from sceneforge.core.provider import Provider
from sceneforge.runtime import ProcessingContext


class Pipeline:
    """
    Sequential provider pipeline.

    Executes providers in registration order.
    """

    def __init__(
        self,
        providers: Iterable[Provider],
    ) -> None:

        self._providers = tuple(providers)

    def run(
        self,
        artifacts: Iterable[Artifact],
        *,
        context: ProcessingContext | None = None,
    ) -> Iterable[Artifact]:

        result = artifacts

        for provider in self._providers:
            result = provider.process(
                result,
                context=context,
            )

        return result
