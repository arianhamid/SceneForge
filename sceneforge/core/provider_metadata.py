from dataclasses import dataclass

from sceneforge.core.capability import Capability


@dataclass(frozen=True, slots=True)
class ProviderMetadata:
    name: str

    version: str

    description: str

    capabilities: frozenset[Capability]
