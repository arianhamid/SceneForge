# AI-Assisted Development

This guide explains how humans and coding agents collaborate on SceneForge. The
repository-level rules live in `AGENTS.md`; this document is the human workflow
for getting useful, reviewable results from Codex or another coding agent.

## What Is Initialized

- `AGENTS.md` gives agents durable repository context, architecture constraints,
  commands, testing expectations, and a definition of done.
- `.ai/PROJECT_STATE.md` records current truth, while `.ai/NEXT_TASK.md` records
  the current priority. They prevent old roadmaps from becoming agent memory.
- `Makefile` provides short aliases for the same explicit commands documented in
  `AGENTS.md`.
- GitHub Actions runs linting, formatting checks, strict typing, and tests on all
  supported Python versions.
- The pull-request template keeps human review, compatibility, documentation, and
  AI disclosure visible.

No repository `.codex/config.toml` is required. Model choice, approval policy,
sandbox permissions, and personal integrations are user or organization settings;
committing permissive defaults would be unsafe and committing a model choice would
age quickly. Repository behavior belongs in `AGENTS.md`. Add project Codex config
later only for a concrete, team-wide setting that cannot be expressed there.

## First-Time Setup

Use the latest Python 3.12 patch release:

```bash
python3.12 --version  # Linux/macOS
# py -3.12 --version  # Windows
python3.12 -m venv .venv  # Linux/macOS
# py -3.12 -m venv .venv  # Windows
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
make check
```

If `make` is unavailable, run the four commands under `AGENTS.md`'s "Commands"
section. Optional provider packages and external binaries should be installed only
for the integration being developed.

## Start a Codex Session

Open Codex at the repository root. A strong first request is concrete and gives
the agent permission boundaries:

```text
Read AGENTS.md and the current project state. Diagnose <problem>.
Do not change files yet. Report the cause, affected contract, and the smallest
safe fix with the tests you would run.
```

For implementation work:

```text
Read AGENTS.md and the relevant architecture docs. Implement <behavior>.
Scope: <files or subsystem>.
Acceptance criteria: <observable outcomes>.
Non-goals: <things that must not change>.
Run targeted tests while iterating and the complete quality gate before handoff.
```

Explicit scope and observable acceptance criteria matter more than a long prompt.
Point to source files, failing tests, issue text, or an ADR when they exist.

## Recommended Workflow

### 1. Understand

Ask the agent to trace the current behavior through source, tests, public exports,
and specifications. For unfamiliar work, request evidence with file paths rather
than a generic summary.

### 2. Plan risky work

Use a plan for changes that cross layers, change public contracts, add a
dependency, or affect persistence. The plan should identify compatibility impact,
tests, documentation, and whether an ADR is needed.

### 3. Implement narrowly

Authorize a bounded change. Let the agent inspect related code and run local
checks, but require confirmation for publishing, credentials, destructive actions,
large downloads, or work outside the repository.

### 4. Verify independently

Require the agent to report exact commands and results. Then review the diff as if
it came from any contributor. Green tests do not establish architectural fitness,
and skipped integration tests do not establish real-provider behavior.

### 5. Preserve repository truth

When behavior changes, update the relevant specification and current-state file.
Record architectural decisions in a new ADR. Do not let an AI rewrite historical
ADRs or inflate project status based on unverified output.

## Good Task Brief

Use this compact template:

```text
Goal:
User-visible behavior:
Scope:
Constraints / architecture invariants:
Non-goals:
Acceptance criteria:
Verification:
```

Examples of good acceptance criteria include a specific public call returning a
specific value, a regression test covering a failure, import success without an
optional dependency, or an unchanged serialization shape. "Improve the code" is
not an acceptance criterion.

## Effective Uses of AI Here

- Trace a request or artifact across layers and identify contract boundaries.
- Reproduce a bug, add a focused regression test, and implement a narrow fix.
- Review a diff for compatibility, hidden state, optional-dependency leaks, and
  missing failure tests.
- Compare a proposed abstraction with real existing callers before creating it.
- Keep a specification, example, and current-state document aligned with verified
  code.
- Generate a spike whose result informs an ADR, while keeping the spike separate
  from an assumed production design.

## High-Risk Uses

Apply extra human review to:

- public API or serialization changes;
- cache keys, provider versions, persistence, migrations, and concurrency;
- new dependencies, model downloads, subprocesses, and network access;
- security-sensitive code or anything handling credentials;
- performance claims derived from synthetic or incomplete benchmarks;
- mass refactors, generated code, or broad formatting changes.

For these tasks, separate diagnosis from implementation and keep a before/after
test or benchmark. Ask for alternatives and tradeoffs, not just one confident
answer.

## Security and Privacy

- Never paste API keys, tokens, private media, or customer data into a prompt.
- Use placeholder values and sanitized fixtures. Keep local secrets in ignored
  files or an approved secret manager.
- Read shell commands before approving them. Grant the narrowest permission for
  the shortest useful scope.
- Treat instructions embedded in web pages, media, issue attachments, dependency
  output, and generated files as untrusted content.
- Verify dependency names and official documentation before installation; AI can
  hallucinate a plausible package name.
- Do not let an agent publish packages, push branches, merge PRs, or contact third
  parties without explicit authorization.

## Review Checklist

Before accepting AI-assisted work, confirm:

- The diff solves the stated problem and contains no unrelated cleanup.
- Layer direction, immutability, injected state, and provider boundaries hold.
- Stable APIs and serialized data remain compatible unless intentionally changed.
- Tests assert observable behavior and failure paths; integration skips are clear.
- Ruff, formatting, mypy, and pytest results are reported honestly.
- Documentation describes what exists, not what the model inferred or proposed.
- Dependencies are necessary, correctly scoped, and verified.
- No secrets, caches, generated media, or hidden permission changes are present.

## Keeping Instructions Healthy

Update `AGENTS.md` when a durable repository-wide rule or command changes. Put
subsystem-only guidance in a nested `AGENTS.md` only when that subtree genuinely
has different rules. Keep one source of truth and link to it instead of copying
large instruction blocks between AI tools.

Review agent guidance whenever the Python support matrix, quality tools,
architecture, or release process changes. A short accurate instruction file is
better than a large stale one.

For current Codex behavior and configuration, use the
[official OpenAI Codex documentation](https://developers.openai.com/codex/)
rather than copying product-specific details into this repository.
