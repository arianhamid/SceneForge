# Codex Project Setup

SceneForge's durable Codex instructions live in the repository-root
`AGENTS.md`. Current implementation context lives in `.ai/PROJECT_STATE.md`, and
the active priority lives in `.ai/NEXT_TASK.md`.

This directory intentionally contains no committed `config.toml`. Model choice,
reasoning defaults, approval policy, sandbox permissions, MCP servers, and account
integrations are personal or organization-managed settings. Committing them here
would either age quickly or change contributors' security posture.

Add project configuration only when SceneForge has a concrete team-wide Codex
setting that cannot be expressed as repository guidance. Never commit credentials
or permissive approval/sandbox overrides.

See `docs/guides/AI_ASSISTED_DEVELOPMENT.md` for setup, prompt templates, safe
permission practices, and review expectations.
