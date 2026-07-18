# Provider Registry Specification

## Purpose

The Provider Registry maintains the collection of available
providers.

## Responsibilities

- Register providers
- Discover providers
- Prevent duplicate names
- Query by capability

## Non Responsibilities

The registry does NOT:

- Execute providers
- Build pipelines
- Manage plugins
- Load configuration

## Usage

```python
from sceneforge.core.registry import Registry
from sceneforge.core.capability import Capability
from sceneforge.contrib.ffmpeg import FFmpegFrameExtractionProvider
from sceneforge.contrib.scenedetect import PySceneDetectProvider
from sceneforge.contrib.whisper import WhisperTranscribeProvider

registry = Registry()
registry.register(FFmpegFrameExtractionProvider())
registry.register(PySceneDetectProvider())
# registry.register(WhisperTranscribeProvider(model))  # needs a real model instance

video_capable = registry.by_capability(Capability.DETECT_SCENES)
provider = registry.get("pyscenedetect")
```

## Known gap (closed, ADR-0017)

`Registry` and `Pipeline` are not wired together — `Pipeline` still
takes a single `provider` directly in its constructor, and nothing
currently uses `Registry.by_capability()` to pick a provider
automatically. This was tracked as an open question through Sprint 8;
`docs/adr/0017-registry-pipeline-rfc-closed.md` formally closed it in
Sprint 9 after six sprints with zero real callers needing runtime
provider selection, per `docs/philosophy/VISION.md` principle 7
("prove it before you formalize it"). `Registry` remains available and
functional for manual capability lookup (see `examples/core/registry_basic.py`);
what's closed is only the question of `Pipeline` wiring to it
automatically. Reopens if real evidence of a need appears — see the
ADR for what that would look like.
