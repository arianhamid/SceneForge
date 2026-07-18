# Contributing

Thank you for your interest in SceneForge.

## Philosophy

We value:

- clean architecture
- readable code
- documentation
- reproducibility
- benchmarking

over clever shortcuts.

## Before writing code

Please read:

- README.md (start here — has a working Quick Start you can actually run)
- docs/philosophy/VISION.md
- docs/architecture/OVERVIEW.md and LAYERS.md
- docs/guides/ADDING_A_PROVIDER.md (if you're implementing a capability)
- .ai/PROJECT_STATE.md (the live, current-state snapshot — check this
  before assuming anything in an older doc is still accurate)
- .ai/NEXT_TASK.md (what's actually being worked on right now)

## Pull Requests

Every PR should:

- include tests when applicable (see `docs/NAMING_CONVENTIONS.md` and
  `docs/guides/ADDING_A_PROVIDER.md` step 7 for what "applicable"
  means for a new provider specifically)
- update documentation — including `.ai/PROJECT_STATE.md` if it
  changes what's actually true about the project's current state
- avoid breaking architecture (see `docs/architecture/LAYERS.md`'s
  dependency rules)
- follow `docs/STYLE_GUIDE.md` and `docs/NAMING_CONVENTIONS.md`; run
  `ruff check --fix`, `ruff format`, and `mypy --strict` before
  submitting — CI enforces both with zero tolerance

## Questions

Discussions are encouraged before implementing large features.
