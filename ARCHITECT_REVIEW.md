
# Chief Architect Review

## Strengths
- Excellent repository organization.
- Strong documentation-first approach.
- Good separation of core/runtime/plugins.
- Clean exception hierarchy already established.

## Recommended changes
1. **Remove `base_provider.py`**: This file exists but isn't used anywhere. The `Provider` ABC already defines the interface. Delete `sceneforge/core/base_provider.py` and ensure no imports reference it.
2. **Replace `ValueError` with framework exceptions**: Create `InvalidNameError(SceneForgeError)` in `exceptions.py` for naming validation, and `InvalidMetadataError(SceneForgeError)` for metadata validation. Update `naming.py` and `validation.py` to use these.
3. **Avoid wildcard imports in package `__init__.py`**: Replace `from sceneforge.core import *` and `from sceneforge.runtime import *` with explicit imports of the public API. Define `__all__` in the top-level `__init__.py`.
4. **Add CI with Ruff, mypy, and coverage**: Create `.github/workflows/ci.yml` with a matrix of Python 3.10-3.12. Include steps for: `ruff check`, `mypy sceneforge/`, `pytest --cov=sceneforge --cov-report=xml`, and `coverage report --fail-under=80`.
5. **Expand test coverage**: Add tests for `Registry.__len__`, `Registry.__contains__`, and edge cases like registering providers with empty capabilities. Add a test for the full plugin lifecycle (register → use → unregister).
6. **Keep `ArtifactKind` inside `artifact.py`**: Already satisfied. No action needed.
7. **Implement FFmpeg frame extraction provider**: Create `sceneforge/contrib/ffmpeg.py` with a `FFmpegProvider` that implements `Capability.FRAME_EXTRACTION`. This will validate the architecture end-to-end.

## Next implementation target
Implement `FFmpegProvider` to extract frames from video files, proving the provider pattern works with a real-world use case.
