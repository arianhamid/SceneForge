registry = ProviderRegistry()

registry.register(JoyCaptionProvider())

registry.register(WhisperProvider())

captioners = registry.by_capability(
    Capability.CAPTION
)

for provider in captioners:
    print(provider.name)
