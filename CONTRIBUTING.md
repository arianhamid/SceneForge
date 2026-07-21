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
- AGENTS.md (the repository-wide implementation and verification contract)
- docs/guides/AI_ASSISTED_DEVELOPMENT.md (when using Codex or another AI tool)
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
  `make check` (or the explicit non-mutating commands in `AGENTS.md`) before
  submitting — CI enforces linting, formatting, strict typing, and tests

## Questions

Discussions are encouraged before implementing large features.

## AI-assisted contributions

AI assistance is welcome, but the contributor remains responsible for every
change. Review generated code and commands, disclose substantial AI assistance in
the pull request, never provide secrets or private media to a model, and report
verification results and skipped checks accurately. `AGENTS.md` applies to both
human and AI-authored changes.
