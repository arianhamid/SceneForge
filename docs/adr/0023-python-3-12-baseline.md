# ADR-0023: Python 3.12 Baseline

## Status

Accepted

## Context

SceneForge previously supported Python 3.11 and 3.12 while local development,
typing, linting, and CI could each select a different interpreter. The project is
still pre-alpha, and maintaining two feature releases adds compatibility surface
without a demonstrated downstream requirement for Python 3.11.

## Decision

Python 3.12 is the sole supported feature release. `requires-python` constrains
the project to `>=3.12,<3.13`; Ruff and mypy target 3.12; CI installs the floating
`3.12` release so it receives the latest available security patch; local setup
creates a 3.12 virtual environment.

The repository does not commit a patch-level `.python-version`. Patch releases
must be allowed to advance without changing source control, and contributors may
use pyenv, uv, a system interpreter, or another environment manager.

## Consequences

- Python 3.11 installations can no longer install SceneForge.
- Python 3.12 language and standard-library features may be used directly.
- Python 3.13 remains unsupported until it is deliberately verified and adopted.
- CI and local verification now exercise the same Python feature release.
