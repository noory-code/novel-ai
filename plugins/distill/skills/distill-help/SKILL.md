---
name: distill-help
user-invocable: true
description: Explain Distill's local knowledge store and the capabilities available on the current host.
metadata:
  version: "1.9.1"
  category: meta
  type: unit
  style: guide
  triggers: [distill help, how to use distill, distill get started]
  uses: []
---

# Distill

Distill stores reusable decisions, patterns, preferences, mistakes, and
workarounds in local project, workspace, and global scopes.

## Every supported host

| Skill | Outcome |
|---|---|
| `distill-init` | Create configuration and inspect the local environment |
| `distill-recall` | Search stored knowledge |
| `distill-profile` | Report scope statistics and status |
| `distill-digest` | Find duplicates and stale entries |
| `distill-memory` | Promote, demote, or delete an exact entry |

Codex and Gemini can also store model-extracted chunks directly through the
`store` MCP tool. They do not receive Sampling-backed extraction tools.

## Claude Code additions

Claude Code loads the additional `distill-learn`, `distill-ingest`, and
`distill-crystallize` skills. These use MCP Sampling or `claude -p`; the
Claude-only session hook can extract knowledge automatically at PreCompact and
SessionEnd.

Start with `distill-init`, then call `distill-recall` at the beginning of work
where prior decisions or patterns may matter.
