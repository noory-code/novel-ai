# Distill

**Short-term memory fades. Distill makes it permanent.**

Claude Code's built-in `/memory` lives in a single session. Distill automatically extracts decisions, patterns, and hard-won insights from every conversation — and makes them available across all your projects, forever.

**No API key needed.** Distill uses MCP Sampling, routing through your existing Claude subscription.

## Why Distill?

Every time you correct Claude, establish a pattern, or choose between approaches, that knowledge disappears when the session ends. The next conversation starts from zero.

Distill captures what matters — automatically, in the background — and builds a permanent, searchable knowledge base that grows with your work.

| | Claude Code `/memory` | `CLAUDE.md` | **Distill** |
|--|--|--|--|
| Scope | Single session | Single project | **Global + per-project** |
| Lifetime | Ephemeral | Manual maintenance | **Permanent, auto-updated** |
| Extraction | Manual | Manual | **Automatic (hooks)** |
| Recall | None | Full file always loaded | **Semantic search on demand** |
| Scale | ~10 items | Grows unwieldy | **Scales with usage** |

After 50 sessions, Distill has extracted your coding patterns, architectural preferences, and project decisions — and Claude automatically has that context in every future conversation.

## What Gets Captured

When you work with Claude Code, valuable knowledge emerges through conversation. Distill captures it automatically.

**Extraction signals** (ordered by confidence):

1. **Decision signals** — Any moment a direction was set: corrections (either party), convergence after discussion, or selection among alternatives
2. **Explicit preferences** — "always use X", "I prefer Y"
3. **Error resolutions** — An error occurred, root cause found, solution applied
4. **Accumulated patterns** — Repeated code/architecture patterns or consistent decision directions

Each extracted piece is classified by type, scope, and confidence, then stored locally in SQLite with vector + full-text search.

## What Happens After init()

Run `init()` once. After that:

1. **Hooks activate automatically** — every conversation end triggers extraction in the background
2. **`recall()` searches everything** — past projects, current project, global patterns — all at once
3. **`memory("crystallize")`** consolidates chunks into `.claude/rules/distill-*.md` files that Claude Code loads automatically as context in every session

The knowledge base grows passively. You work normally; Distill captures what matters.

## Proven on Distill itself

Evonest evolves Distill's own codebase through the same cycle. Here are real findings from 194 completed proposals:

| Finding | Persona | Outcome |
|---------|---------|---------|
| f-string `WHERE` clauses — SQL injection risk | security-auditor | Fixed: parameterized queries with `?` placeholders throughout |
| Per-chunk embedding calls — 20+ model runs per ingest | performance-analyst | Fixed: batch embedding via `index_many()` — 10–20× faster |
| Single corrupt JSONL line drops entire transcript | chaos-engineer | Fixed: per-line error recovery + UTF-8 boundary truncation |
| `__exit__` doesn't guarantee `close()` on exception | spec-reviewer | Fixed: try/finally + `PRAGMA busy_timeout` for concurrent safety |
| Bare `except Exception: pass` in 19+ locations | spec-reviewer | Fixed: structured logging with `exc_info=True` throughout |

## Installation

### Claude Code Plugin (recommended)

**1. Add marketplace**
```
/plugin marketplace add noory-code/noory-ai
```

**2. Install plugin**
```
/plugin install distill@noory-code/noory-ai
```

MCP server, hooks (PreCompact, SessionEnd), and skills are registered automatically.

### Manual

```bash
git clone https://github.com/noory-code/noory-ai.git
cd noory-ai/distill
uv sync
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

> **Note:** Manual installation does not activate hooks automatically. To enable background extraction after each session, add the hooks from `hooks/hooks.json` to your Claude Code settings manually, or use the plugin install method above.

## Quick Start

```
1. init()
   → creates config, scans environment, ingests configured dirs
   → hooks activate: all future conversations auto-extract knowledge

2. Work normally with Claude Code
   → Distill runs in the background after each session

3. recall("your question here")
   → searches everything: current project, all past projects, global patterns

4. memory("crystallize")   ← optional, recommended
   → consolidates into .claude/rules/distill-*.md
   → Claude Code loads these automatically in every future session
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `init(scope?)` | One-step onboarding: create config, scan environment, ingest configured dirs |
| `recall(query)` | Search your knowledge base by semantic query |
| `learn(transcript_path)` | Extract knowledge from a conversation transcript (auto-crystallize if threshold met) |
| `store(chunks, session_id)` | Save pre-extracted knowledge chunks (no LLM — used by hooks) |
| `ingest(path, scope?)` | Extract knowledge from markdown/text files in a directory |
| `profile()` | View statistics about your accumulated knowledge |
| `digest()` | Find duplicate entries and analyze patterns |
| `memory(action, id)` | promote/demote/delete/crystallize knowledge entries |
| `test_raw_sampling()` | Test MCP sampling connectivity (diagnostic) |

### Usage Examples

**Get started (first time):**
```
init()
```

**Search for knowledge:**
```
recall("how to handle authentication in this project")
```

**Crystallize into rule files:**
```
memory("crystallize")
```

**Manage knowledge scope:**
```
memory("promote", "chunk-id")      # move one step up (project → workspace → global)
memory("demote", "chunk-id")       # move one step down (global → workspace → project)
memory("delete", "chunk-id")       # remove entry
```

## Knowledge Types

| Type | Description | Example |
|------|-------------|---------|
| `pattern` | Recurring code/architecture conventions | "Always use barrel exports in this project" |
| `preference` | Explicit user preferences | "Prefer functional style over class-based" |
| `decision` | Architectural or technology choices | "Chose SQLite over PostgreSQL for local storage" |
| `mistake` | Corrections and lessons learned | "Don't use `any` type — use `unknown` instead" |
| `workaround` | Bug workarounds and edge cases | "Library X has a bug with Y — use Z instead" |
| `conflict` | Contradictions with existing rules | "New pattern conflicts with distill-style.md rule #2" |

## Scope

Knowledge is stored in three scopes — all searched simultaneously by `recall`:

| Scope | Path | Purpose |
|-------|------|---------|
| `global` | `~/.distill/knowledge/` | Language/framework patterns — portable across all projects |
| `workspace` | `<git-root>/.distill/knowledge/` | Shared monorepo conventions |
| `project` | `.distill/knowledge/` | Project-specific decisions |

The global scope is your permanent, cross-project knowledge base. Patterns extracted from project A are available when you start project B.

Use `memory("promote", id)` to move knowledge up (project → workspace → global), or `memory("demote", id)` to move it down.

## Configuration

See [docs/configuration.md](docs/configuration.md) for detailed setup instructions.

## Architecture

See [docs/architecture.md](docs/architecture.md) for technical details and system diagrams.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

[MIT](LICENSE)
