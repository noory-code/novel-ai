# Privacy Policy

**Distill** is a Claude Code plugin that operates entirely on your local machine.

## Data Collection

Distill does **not** collect, transmit, or store any data on external servers.

## How Data Is Stored

Knowledge extracted from conversations is stored locally in SQLite databases at three scopes:

| Scope | Location | Purpose |
|-------|----------|---------|
| Global | `~/.distill/` | Knowledge shared across all projects |
| Workspace | `<git-root>/.distill/` | Knowledge shared within a git workspace |
| Project | `.distill/` | Project-specific knowledge |

You have full control over stored data:
- View entries: `recall(query)` or `profile()`
- Delete entries: `memory("delete", id)`
- Remove all data: delete the `.distill/` directories

## Knowledge Extraction

Distill uses **MCP Sampling** to extract knowledge from conversations. MCP Sampling routes through your existing Claude subscription (Claude Code, Claude Max, or Claude Teams) — no separate API key is required. The extraction happens locally between Claude Code and the Distill MCP server on your machine.

## Third-Party Services

Distill does not integrate with or send data to any third-party services.

## Changes to This Policy

Updates will be documented in the [CHANGELOG](./CHANGELOG.md) and reflected in the plugin version.

## Contact

For questions, open an issue at [github.com/noory-code/noory-ai](https://github.com/noory-code/noory-ai/issues).

---

*Last updated: 2026-03-17 | Distill v1.4.0*
