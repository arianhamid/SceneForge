# ADR 0010: Model-Backed Providers Take Their Model as a Constructor Argument

## Status

Accepted

## Context

`sceneforge.contrib.whisper.WhisperTranscribeProvider` is the
framework's first provider backed by a real inference model rather
than a subprocess (`ffmpeg`) or a pure algorithm (`scenedetect`).
Constructing `faster_whisper.WhisperModel` directly downloads weights
from the Hugging Face Hub on first use. That's a real problem for more
than convenience: it makes the provider's *own logic* (path handling,
artifact shaping, error wrapping, segment-to-artifact mapping)
untestable without network access, a GPU, and several hundred
megabytes of weights -- none of which should be a precondition for
verifying `WhisperTranscribeProvider.run()` does the right thing with
a given set of segments.

This is a pattern every future model-backed provider (a captioning
VLM, an embedding model, a face-recognition model) will hit. Deciding
it once, here, prevents each one from re-deriving the same answer
under time pressure.

## Decision

A model-backed `Provider` takes its model as a constructor argument,
typed against a small structural `Protocol` (`WhisperModelProtocol`)
derived from the real library's actual method signature -- not a
guess, not the full surface of the real class, just the methods the
provider actually calls. The provider never imports the real model
library at module level; it only depends on the Protocol shape.

Concretely:

```python
class WhisperTranscribeProvider(Provider):
    def __init__(self, model: WhisperModelProtocol, **transcribe_kwargs: Any) -> None:
        self._model = model
```

A caller who wants the real thing constructs it explicitly and passes
it in:

```python
from faster_whisper import WhisperModel
provider = WhisperTranscribeProvider(WhisperModel("small", device="cpu"))
```

A test injects a lightweight fake satisfying the same Protocol, with
no weights and no network:

```python
provider = WhisperTranscribeProvider(FakeWhisperModel([...]))
```

One additional contract test checks the *real* library's class shape
against the Protocol without instantiating it (`hasattr(WhisperModel,
"transcribe")`), so the Protocol can't silently drift from what the
real library actually exposes.

## Consequences

- `WhisperTranscribeProvider` has ten unit tests, zero of which touch
  the network, a GPU, or download anything -- see
  `tests/contrib/test_whisper_transcribe.py`.
- The provider is also, as a direct consequence, agnostic to *which*
  concrete model backs it: any object satisfying
  `WhisperModelProtocol` works, including a future non-Whisper STT
  library with a compatible `transcribe()` shape, or a remote API
  client wrapped to look the same locally.
- Model construction (size, device, compute type -- real resource
  decisions) is explicitly the caller's responsibility, not something
  the provider decides via a hardcoded default. This matches
  `docs/philosophy/VISION.md` principle 3 ("capabilities before
  models") one level deeper than capability *selection* -- it also
  applies to model *configuration*.
- This is now the documented, expected pattern for the next
  model-backed provider (see `docs/guides/ADDING_A_PROVIDER.md` step
  3) rather than something each provider author has to rediscover.

## Alternatives Considered

1. Construct the model inside the provider from a `model_size` string
   argument, matching how a lot of example code for these libraries is
   written -- rejected: makes every unit test either need real weights
   or reach for `unittest.mock.patch` on the model library's internals,
   which is both slower to write and more brittle (breaks silently if
   the library's internal construction path changes) than a Protocol
   the provider actually owns.
2. A framework-wide "model registry" that lazily constructs and caches
   model instances by name -- rejected for now as speculative; nothing
   in the codebase needs to share a model instance across providers
   yet, and building that abstraction before a second model-backed
   provider exists risks designing it around an imagined need (see
   `docs/philosophy/VISION.md` principle 7).
