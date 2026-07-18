# Style Guide

Also previously an empty file. This describes what the codebase
already does consistently — it's a description of practice, not an
aspiration.

## Formatting and linting

- `ruff` is the source of truth for formatting and lint (see
  `pyproject.toml`'s `[tool.ruff]`). Run `ruff check --fix` and
  `ruff format` before committing; CI runs `ruff check` with zero
  tolerance for violations.
- `mypy --strict` is the source of truth for typing. Every public
  function and method has a full type signature. `Any` is allowed only
  at genuine type-erasure boundaries (e.g. `Artifact[Any]` when a
  Pipeline doesn't know a specific provider's payload type) — never as
  a way to silence an error you don't understand.
- Line length: 88 characters (ruff/black default). Prefer breaking a
  call's arguments one-per-line over a trailing `# noqa`.

## Docstrings

- Every public module opens with a docstring explaining *why the
  module exists*, not just what's in it — see any file under
  `sceneforge/core/` for the expected depth. A docstring that only
  restates the class name in prose is not sufficient.
- Class and method docstrings use Google-style `Args:`/`Returns:`/
  `Raises:` sections when the signature has more than one non-obvious
  parameter or can raise.
- When a design decision was contested or non-obvious (e.g. why
  `Pipeline` retries a provider instead of failing fast by default —
  it doesn't; `max_retries=0`), the docstring says so, briefly. Silent
  cleverness is a bug report waiting to happen.

## Immutability discipline

- `Media` and `Artifact` are `@dataclass(frozen=True, slots=True)`.
  Never work around frozen-ness with `object.__setattr__` outside
  `__post_init__`. Need to change a field? Use `Media.evolve()` /
  `dataclasses.replace()` and return a new instance.
- Mutable framework state (a `Pipeline`'s retry count, a
  `ProcessingContext`'s cancellation flag) is explicitly *not*
  `frozen` and says so in its docstring, so the two categories are
  never confused at a glance.

## Errors

- Raise a `SceneForgeError` subclass, never a bare `Exception` or a
  standard-library exception, at any framework boundary a caller might
  reasonably catch. Wrap third-party/standard-library exceptions with
  `raise SomeSceneForgeError(...) from original_exc` so the traceback
  is preserved.
- Catching `Exception` broadly is allowed *only* at a boundary that
  must isolate a third-party call from breaking the framework's own
  control flow (see `Pipeline.run_detailed`'s provider-call try/except,
  or `AsyncPipeline.run_many`'s per-item isolation) — and always
  re-raises or records the original exception, never swallows it
  silently.

## Imports

- Absolute imports only (`from sceneforge.core.artifact import
  Artifact`), even within the same package — no implicit relative
  imports. `from __future__ import annotations` at the top of every
  module that uses modern generic syntax, for compatibility with the
  minimum supported Python version.
- `TYPE_CHECKING`-guarded imports for anything used only in type
  hints, to avoid import cycles between layers that would otherwise be
  fine at type-check time but wrong at runtime.
