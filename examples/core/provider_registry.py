from sceneforge.core.registry import Registry

registry = Registry()

registry.register(WhisperProvider())

registry.register(FFmpegProvider())

for provider in registry.providers():

    print(provider.metadata.name)
