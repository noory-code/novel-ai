# CLAUDE.md

This file provides guidance to Claude Code and Codex when working in this repository.

## Repository Structure

`novel-ai` is the open plugin stack used by Novel. The four packages are independently installable
and deliberately exchange files and stable identifiers instead of importing one another.

```
novel-ai/
├── mashbill/  — Novel canvas, MCP/HTTP server, skills, agents, and hooks
├── solera/    — deterministic work planning and execution harness
├── proof/     — append-only decision log
└── distill/   — durable knowledge extraction and recall
```

Each package owns its `pyproject.toml`, `uv.lock`, tests, manifest, and changelog. There is no root
Python workspace. Run development commands from the package being changed.

## Commands

```bash
cd <package>
uv sync
uv run pytest
uv run mypy <package-or-src>/ tests/
uv run ruff check <package-or-src>/ tests/
uv run ruff format <package-or-src>/ tests/
```

Mashbill also contains frontend assets and package-specific gates. Read
`mashbill/CLAUDE.md` in full before changing anything under `mashbill/`.

## Language

- Write documents, comments, commit messages, and code artifacts in English.
- Converse with the repository owner in Korean.

## Core Principles

### SSOT

- Link to existing information instead of duplicating it.
- Give each datum one canonical location.

### MECE

- New categories must not overlap existing ones.
- Check for missing cases before considering work complete.

### Separation of Concerns

- Keep each module focused on one responsibility.
- Review a file for splitting when it exceeds 500 lines.

### Atomic, Incremental Changes

- Each commit must have one purpose and pass its relevant checks.
- Use `type(scope): description` commit messages in English.
- Preserve the independence boundary: no package may import a sibling package.

## Plugin Changes

Any modification inside a plugin directory requires all of the following in the same package:

1. Bump the plugin version: patch for fixes/docs/packaging, minor for features or refactors.
2. Update the package's version SSOTs together:
   - Mashbill: `mashbill/mashbill/__init__.py` and `mashbill/.claude-plugin/plugin.json`
   - Solera: `solera/pyproject.toml` and `solera/.claude-plugin/plugin.json`
   - Proof: `proof/pyproject.toml` and `proof/.claude-plugin/plugin.json`
   - Distill: `distill/pyproject.toml` and `distill/.claude-plugin/plugin.json`
3. Add a dated entry to that package's `CHANGELOG.md`.
4. Run the package's tests and static checks before committing.

## Cross-Platform Compatibility

All runtime code must support macOS, Linux, and Windows.

| Avoid | Use |
|---|---|
| Shell scripts for shipped automation | Python scripts |
| Hard-coded `/tmp/` | `tempfile` |
| Unix-only virtualenv paths | Platform-aware paths |
| `fcntl` without a Windows path | `fcntl`/`msvcrt` platform dispatch |
| Shell-only filesystem utilities in shipped scripts | Python stdlib |

Hook commands use `python3` and `${CLAUDE_PLUGIN_ROOT}`. Plugin state belongs in the user's project
or documented data directory, never in the ephemeral installed plugin cache.

## AI-First Documentation

Write conditions, paths, thresholds, and outcomes explicitly. Do not use vague instructions such as
"as appropriate", "if needed", "depending on the situation", "as you see fit", or "handle
accordingly".

## Architecture Boundaries

- Mashbill publishes Novel artifacts; Solera imports published artifacts by value.
- Solera may reference Proof decision identifiers and Mashbill artifact identifiers, but it does
  not import either package.
- Proof is a lower-layer substrate and imports no sibling package.
- Distill remains independent of the Novel application and every sibling plugin.
- Package-level independence tests are the executable contract; keep them green.
