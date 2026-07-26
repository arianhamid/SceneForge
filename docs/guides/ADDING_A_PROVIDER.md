# Guide: Adding a Provider

This is the doc that didn't exist when this project had zero real
providers, and was sorely missing once it had three. If you're adding
a fourth (an OCR provider, a face-recognition provider, an LLM-based
captioner), this is the checklist. Every step points at one of
`sceneforge.contrib.ffmpeg`, `sceneforge.contrib.scenedetect`, or
`sceneforge.contrib.whisper` as a real, working example — copy the one
closest to your situation rather than starting from a blank file.

## 1. Does the capability already exist?

Check `sceneforge/core/capability.py`. If your provider implements
something already listed (`CAPTION`, `OCR`, `FACE_DETECTION`,
`OBJECT_DETECTION`, `EMBEDDING`, `DETECT_SCENES`, `FRAME_EXTRACTION`,
`TRANSCRIBE`, `AUDIO_ANALYSIS`), skip to step 2.

If not, add it to the `Capability` enum, then register which media
types it supports in `build_default_capability_registry()`
(`sceneforge/core/capability_registry.py`). Don't register a
capability for a media type your provider can't actually handle —
`Pipeline`'s validation is only as good as this mapping.

## 2. Pick your shape: subprocess, algorithmic, or model-based

This determines which existing provider to copy from and whether you
need dependency injection.

| Your provider calls...                          | Copy from                              | Needs injection? |
|---------------------------------------------------|-----------------------------------------|-------------------|
| A CLI tool via `subprocess` (ffmpeg, exiftool)     | `sceneforge.contrib.ffmpeg`             | No — call the binary directly, guard with `shutil.which()` |
| A pure algorithm, no weights, no network (scenedetect, a hash function) | `sceneforge.contrib.scenedetect` | No |
| A model whose trained weights ship *inside* the library's own package (OpenCV's Haar cascades) | `sceneforge.contrib.opencv` | No — check this before assuming "model-backed" means injection; see `docs/adr/0015-opencv-face-detection.md` |
| A model that needs weights downloaded separately (Whisper, a VLM, an embedding model) | `sceneforge.contrib.whisper`  | **Yes** — see step 3 |

The middle two rows are easy to conflate. The real test isn't "does
this use a trained model" — it's "do the weights already exist on disk
the moment the package is installed, with no separate download step."
`cv2.data.haarcascades` does; `WhisperModel("small")`'s first call
doesn't. Check this explicitly (try constructing the real thing
without network access) before reaching for dependency injection —
it's extra ceremony a bundled-weights provider doesn't need.

## 3. If your provider needs model weights: inject the model

This is the one non-obvious lesson from this codebase: **do not
construct the model object inside your `Provider.__init__` or
`run()`**. Take it as a constructor argument instead.

Why: constructing a real model (a `WhisperModel`, a captioning VLM
client, anything that downloads or loads weights) is slow, needs a
GPU or a lot of RAM, and — critically — usually needs network access
the first time. None of that should be a precondition for *testing*
your provider's logic (path handling, artifact shaping, error
wrapping). See `sceneforge/contrib/whisper/provider.py`'s module
docstring for the full reasoning, and
`tests/contrib/test_whisper_transcribe.py` for what this buys you: ten
tests, zero network calls, zero GPU, zero downloaded weights.

The pattern:

```python
from typing import Protocol, runtime_checkable


@runtime_checkable
class MyModelProtocol(Protocol):
    def infer(self, input_path: str) -> MyModelOutput: ...


class MyProvider(Provider):
    def __init__(self, model: MyModelProtocol) -> None:
        self._model = model

    # ...
```

Define the Protocol by *reading the real library's actual method
signature* (`inspect.signature(RealClass.method)` in a Python shell —
you don't need to construct an instance to do this), not by guessing.
Add one cheap test that checks the real class has the expected method,
without instantiating it:

```python
def test_real_model_shape_is_compatible():
    real_lib = pytest.importorskip("my_model_library")
    assert hasattr(real_lib.MyModelClass, "infer")
```

## 4. Write the Artifact

One dataclass per artifact type your provider produces, in its own
file next to the provider:

```python
@register_artifact_type
@dataclass(frozen=True, slots=True)
class MyArtifact(Artifact[PayloadType]):
    media_id: UUID = field(default_factory=uuid4)
    # ... your specific fields ...
    kind: ArtifactKind = ArtifactKind.SOMETHING  # add to the enum if new
    provider: str = "my_provider"
```

`@register_artifact_type` is not optional if you want this artifact
to round-trip through `Pipeline(..., store=...)` as its actual type
instead of the generic base `Artifact` — see
`docs/adr/0008-artifact-persistence.md`.

## 5. Write the Provider

```python
class MyProvider(Provider):
    @property
    def name(self) -> str:
        return "my_provider"  # used in cache keys — pick something stable

    @property
    def version(self) -> str:
        return "1.0.0"  # bump this whenever output would change for the same input

    @property
    def capabilities(self) -> frozenset[Capability]:
        return frozenset({Capability.MY_CAPABILITY})

    def run(self, media: Media) -> list[Artifact[Any]]:
        if not isinstance(media, ExpectedMediaType):
            raise TypeError(f"Expected ExpectedMediaType, got {type(media).__name__}")

        source = media.metadata.get("source")
        if not source:
            raise ProviderError("...")

        try:
            result = self._model.infer(str(source))  # or subprocess, or pure computation
        except Exception as exc:
            raise ProviderError(f"...: {exc}") from exc

        return [MyArtifact(media_id=media.id, provider=self.name, ...)]
```

Rules that are easy to violate accidentally, all three real providers
follow them, and `PROVIDER_SPEC.md`/`STYLE_GUIDE.md` will call it out
in review:

- Never catch an exception silently — wrap it in a `SceneForgeError`
  subclass (usually `ProviderError`) with `from exc` so the original
  traceback survives.
- `version` is part of the `ArtifactStore` cache key. If you change
  what the provider actually produces for the same input (a prompt
  tweak, a post-processing change, a model upgrade), bump it — nobody
  else can catch a forgotten bump for you.
- Type-check the `Media` you receive and raise `TypeError` immediately
  if it's wrong, rather than letting an `AttributeError` happen three
  lines later inside your logic.

## 6. If your provider is slow (model inference, an API call): stay synchronous, wrap with `SyncProviderAdapter`

Don't write an async version of your provider unless the underlying
library is natively async (rare). Write a plain synchronous `Provider`
as above, and let callers who need concurrency wrap it:

```python
from sceneforge.core.async_provider import SyncProviderAdapter
from sceneforge.core.async_pipeline import AsyncPipeline

pipeline = AsyncPipeline(SyncProviderAdapter(MyProvider(model)), max_concurrency=3)
batch = await pipeline.run_many(media_items)
```

See `sceneforge.contrib.whisper` for the reference example and
`docs/adr/0009-async-providers.md` for why this is the right default.

## 7. Tests

At minimum, matching what all three real providers have:

- One test per failure mode your `run()` can hit (wrong media type,
  missing `source`, the underlying call raising).
- One test proving the happy path produces the artifacts you expect,
  with correct field values — not just "doesn't crash."
- If model-based: the fake-model unit tests from step 3, plus the
  cheap real-class-shape contract test.
- If subprocess- or algorithm-based and the tool is free to run in any
  environment (no weights, no network): a *real* integration test
  against a generated fixture, like
  `tests/contrib/test_ffmpeg_integration.py` and
  `tests/contrib/test_scenedetect_integration.py`. Mocking a tool that
  could just be run for real produces false confidence.
- Run through `Pipeline`/`AsyncPipeline` at least once in a test, not
  just the provider in isolation — the pipeline's enrichment/caching/
  retry behavior around your provider is part of what "the provider
  works" means in practice.

## 8. Update the docs this guide didn't cover

- `docs/specifications/PROVIDER_SPEC.md`: add your provider to "The
  first real Provider" section (rename it if there are now several —
  it's fine for this doc to have a running list).
- `docs/architecture/DOMAIN_MODEL.md`'s Provider examples.
- `pyproject.toml`: add an optional-dependency extra if your provider
  needs a third-party package (`scenedetect`, `whisper` are the
  existing examples).
- `.ai/PROJECT_STATE.md` and `.ai/NEXT_TASK.md`: update "Known
  Problems" / "Completed" so the next person (or the next AI session)
  isn't planning around stale information.

## Anti-patterns seen (and fixed) in this codebase — don't reintroduce them

- **Don't** construct a model, open a network connection, or read
  global config inside `__init__` or `run()` when it could be injected
  instead — see step 3.
- **Don't** add a new module-level mutable dict for provider-specific
  state "just this once" — see `docs/adr/0007-injectable-capability-registry.md`
  for what that turns into.
- **Don't** let a provider's `run()` mutate the `Media` it receives.
  If your provider discovers something that should correct `Media`
  metadata (not just produce an `Artifact`), that's a `MediaEnricher`,
  not a `Provider` — see `docs/specifications/PROVIDER_SPEC.md`'s
  "MediaEnricher" section.
- **Don't** write a docstring claiming behavior you haven't actually
  implemented (`STYLE_GUIDE.md`). If it's aspirational, say so
  explicitly, the way `docs/architecture/DOMAIN_MODEL.md`'s Pipeline
  section now does for provider composition.
