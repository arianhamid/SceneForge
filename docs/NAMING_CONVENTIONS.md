# Naming Conventions

This file used to exist and be empty, which is worse than not
existing — it implied naming was specified somewhere when it wasn't.
This is the real, short version, derived from the conventions already
consistently used across `sceneforge/`.

## Modules and packages

- Package names: `snake_case`, singular where the package represents
  one concept (`sceneforge.core`), plural where it's a collection
  (`sceneforge.contrib`, `sceneforge.plugins`).
- One primary class per file; the file is named after the class in
  `snake_case` (`pipeline.py` → `Pipeline`, `capability_registry.py` →
  `CapabilityRegistry`).

## Classes

- `PascalCase`.
- Protocols are named for the role, not suffixed with `Protocol`
  unless a concrete class of the same name already exists in the same
  layer (e.g. `provider.py`'s `Provider` ABC vs.
  `provider_protocol.py`'s structural `Provider` — imported aliased as
  `ProviderProtocol` at the point of use to disambiguate).
- Exceptions end in `Error` and inherit from `SceneForgeError`
  (`IncompatibleMediaError`, `ProviderExecutionError`).
- Artifact subclasses end in `Artifact` (`IdentityArtifact`,
  `FrameExtractionArtifact`).
- Provider implementations end in `Provider`
  (`FFmpegFrameExtractionProvider`); enrichers end in `Enricher`
  (`FFprobeEnricher`).

## Functions and variables

- `snake_case` for functions, methods, and variables.
- Boolean-returning functions/properties read as a question or
  assertion: `is_compatible()`, `has()`, `all_succeeded`.
- Private/internal attributes are prefixed with a single underscore
  (`self._provider`), never name-mangled with a double underscore
  unless deliberately avoiding a subclass collision.

## Capabilities and artifact kinds

- `Capability` and `ArtifactKind` are `StrEnum` members in
  `SCREAMING_SNAKE_CASE` on the Python side, serializing to
  `lowercase_with_underscores` string values (`Capability.FRAME_EXTRACTION`
  → `"frame_extraction"`). Never introduce a new capability or kind as
  a raw string; add it to the enum.

## Tests

- Test files mirror the module under test:
  `sceneforge/core/pipeline.py` → `tests/core/test_pipeline.py`.
- Test function names are a sentence describing the behavior under
  test, not the method name: `test_retries_are_attempted`, not
  `test_run_2`.
- Integration tests that depend on an external binary being present
  (ffmpeg, ffprobe) live under `tests/contrib/` and are guarded with
  `pytest.mark.skipif` rather than mocked into meaninglessness — see
  `tests/contrib/test_ffmpeg_integration.py`.
