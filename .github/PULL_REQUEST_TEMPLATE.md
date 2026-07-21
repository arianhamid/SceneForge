## Summary

<!-- What changes for users or contributors, and why? -->

## Architecture and compatibility

- [ ] The change respects `docs/architecture/LAYERS.md`.
- [ ] Stable API compatibility is preserved, or the breaking change is explicit.
- [ ] A new or superseding ADR is included when architecture changed.

## Verification

- [ ] Tests cover the new or corrected behavior.
- [ ] `python -m ruff check .`
- [ ] `python -m ruff format --check .`
- [ ] `python -m mypy --strict sceneforge`
- [ ] `python -m pytest -q`

List any skipped checks and the reason:

## Documentation and AI assistance

- [ ] Public docs/examples and `.ai/PROJECT_STATE.md` are updated when needed.
- [ ] Substantial AI assistance is disclosed and all generated changes were human-reviewed.
- [ ] No secrets, local caches, generated media, or unrelated edits are included.
