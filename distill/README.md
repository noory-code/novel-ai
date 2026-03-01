# Distill

**Short-term memory fades. Distill makes it permanent.**

Claude Code's built-in `/memory` lives in a single session. Distill automatically extracts decisions, patterns, and hard-won insights from every conversation — and makes them available across all your projects, forever.

**No API key needed.** Distill uses MCP Sampling, routing through your existing Claude subscription.

## Why Distill?

| | Claude Code `/memory` | `CLAUDE.md` | **Distill** |
|--|--|--|--|
| Scope | Single session | Single project | **Global + per-project** |
| Lifetime | Ephemeral | Manual maintenance | **Permanent, auto-updated** |
| Extraction | Manual | Manual | **Automatic (hooks)** |
| Recall | None | Full file always loaded | **Semantic search on demand** |
| Scale | ~10 items | Grows unwieldy | **Scales with usage** |

After 50 sessions, Distill has extracted your coding patterns, architectural preferences, and project decisions — and Claude automatically has that context in every future conversation.

## What Gets Captured

Distill extracts knowledge automatically, ordered by confidence:

1. **Decisions** — corrections, convergence moments, selection among alternatives
2. **Explicit preferences** — "always use X", "prefer Y"
3. **Error resolutions** — root cause found, fix applied
4. **Patterns** — repeated code/architecture conventions

## What Happens After init()

Run `init()` once. After that:

1. **Hooks activate automatically** *(plugin install only)* — every session end triggers extraction in the background
2. **`recall()` searches everything** — current project, all past projects, global patterns — simultaneously
3. **`memory("crystallize")`** consolidates chunks into `.claude/rules/distill-*.md` files that Claude Code loads automatically as context in every session

The knowledge base grows passively. You work normally; Distill captures what matters.

## Proven on Distill itself

Evonest evolves Distill's own codebase through the same cycle. Real findings from 194 executed proposals:

| Finding | Persona | Outcome |
|---------|---------|---------|
| f-string `WHERE` clauses — SQL injection risk | security-auditor | Fixed: parameterized queries with `?` placeholders |
| Per-chunk embedding calls — 20+ model runs per ingest | performance-engineer | Fixed: batch embedding via `index_many()` — 10–20× faster |
| Single corrupt JSONL line drops entire transcript | chaos-engineer | Fixed: per-line error recovery + UTF-8 boundary truncation |
| `__exit__` doesn't guarantee `close()` on exception | spec-reviewer | Fixed: try/finally + `PRAGMA busy_timeout` |
| Bare `except Exception: pass` in 19+ locations | observability-advocate | Fixed: structured logging with `exc_info=True` throughout |

## Install

### Claude Code Plugin (recommended)

```
/plugin marketplace add noory-code/noory-ai
/plugin install distill@noory-code/noory-ai
```

MCP server, hooks (PreCompact, SessionEnd), and skills are registered automatically.

### Manual

```bash
git clone https://github.com/noory-code/noory-ai.git
cd noory-ai/distill && uv sync
```

Add to `.mcp.json`:

```json
{
  "mcpServers": {
    "distill": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/noory-ai/distill", "python", "-m", "distill"]
    }
  }
}
```

> **Note:** Manual installation does not activate hooks automatically. To enable background extraction, add the hooks from `hooks/hooks.json` to your Claude Code settings manually.

## Quick Start

```
1. init()
   → creates config, scans environment

2. Work normally with Claude Code
   → Distill extracts automatically after each session (plugin install)
   → or run: learn("<transcript_path>") to extract manually

3. recall("your question")
   → searches all scopes: project, workspace, global

4. memory("crystallize")              ← optional, recommended
   → writes .claude/rules/distill-*.md
   → Claude Code loads these automatically in every session

5. memory("promote", "chunk-id")      ← move project knowledge to global
   memory("demote",  "chunk-id")      ← move global to project
   memory("delete",  "chunk-id")      ← remove entry
```

## Scope

Knowledge is stored in three scopes — all searched simultaneously by `recall`:

- **global** (`~/.distill/`) — cross-project patterns, available in every project
- **workspace** (`<git-root>/.distill/`) — monorepo conventions
- **project** (`.distill/`) — project-specific decisions

The global scope is your permanent knowledge base. Patterns from project A are available when you start project B.

## MCP Tools

Full API reference: [docs/tools.md](docs/tools.md)

Core tools: `init`, `recall`, `learn`, `store`, `ingest`, `profile`, `digest`, `memory`, `test_raw_sampling`

## Configuration

See [docs/configuration.md](docs/configuration.md) for all options.

## Architecture

See [docs/architecture.md](docs/architecture.md) for technical details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT](LICENSE)
