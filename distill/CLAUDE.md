# Distill

> MCP server that extracts reusable knowledge from Claude Code conversations.

## Current Work

Phase 2.6 complete (workspace scope, monorepo support, walk-up root detection).
See [ROADMAP.md](ROADMAP.md) for Phase 3+ planning.

## Build & Run

| Command | Action |
|---------|--------|
| `uv sync` | Install dependencies |
| `uv run python -m distill` | Start MCP server |
| `uv run pytest` | Run all tests (311 tests) |

## Architecture

```
src/distill/
├── config.py              ← Config loader (.distill/config.json, SourcesConfig, OutputsConfig)
├── server.py              ← FastMCP server + 8 tool registrations
├── store/                 ← SQLite metadata + FTS5 + sqlite-vec (fastembed embeddings)
│   ├── metadata.py        ← SQLite CRUD + FTS5 full-text search
│   ├── vector.py          ← Vector index (fastembed + sqlite-vec)
│   ├── scope.py           ← Scope detection (global/workspace/project), walk-up root detection
│   └── types.py           ← KnowledgeEntry, KnowledgeInput, KnowledgeSource, KnowledgeScope
├── scanner/               ← .claude/ environment scanner (rules, skills, agents inventory)
│   ├── scanner.py         ← scan_environment() → EnvironmentInventory
│   └── types.py           ← EnvironmentItem, EnvironmentInventory, UserConflict
├── extractor/
│   ├── parser.py          ← .jsonl transcript parsing
│   ├── prompts.py         ← System + user prompt templates (extraction + crystallize)
│   ├── extractor.py       ← Orchestration + MCP sampling call
│   ├── crystallize.py     ← Consolidate chunks → distill-*.md rule/skill/agent files
│   ├── rules_reader.py    ← Read rules from global + project scopes
│   └── sampling_error.py  ← MCP sampling error wrapping
├── tools/                 ← 8 MCP Tools
│   ├── recall.py          ← Semantic search
│   ├── learn.py           ← Extract from transcript (requires LLM)
│   ├── profile.py         ← Knowledge statistics
│   ├── digest.py          ← Duplicate detection + stale analysis
│   ├── memory.py          ← promote/demote/delete/crystallize
│   ├── ingest.py          ← Extract from markdown/text files
│   ├── store.py           ← Save pre-extracted chunks (no LLM)
│   └── init.py            ← One-step onboarding
└── hooks/
    └── distill_hook.py    ← PreCompact/SessionEnd: Anthropic API or claude -p subprocess
shared/prompts.md          ← Extraction prompt SSOT (must sync with prompts.py)
```

## Key Patterns

### Two-Path LLM Architecture

LLM calls use MCP Sampling first, Anthropic API fallback:
- **MCP Sampling** (`ctx.sample()`): Routes through user's Claude subscription — no API key needed. Primary path.
- **Anthropic API fallback**: Used when sampling returns "not supported" (CLI/VSCode). Requires `ANTHROPIC_API_KEY`.
- **`claude -p` subprocess**: Used by hooks when `ANTHROPIC_API_KEY` is not set. Runs extraction immediately at session end — no deferred handoff needed.

`init()` installs distill skills and hooks automatically.

### Hook Auto-Learn Flow

Hooks run outside the MCP server process. At session end:

1. **If `ANTHROPIC_API_KEY` set**: hook calls Anthropic API directly → extracts + stores
2. **If no API key**: hook runs `claude -p` subprocess → `claude -p` reads transcript + calls `mcp__distill__store()`

## MCP Tools

| Tool | Description |
|------|-------------|
| `init()` | One-step onboarding: create config, install skills, scan env |
| `recall(query)` | Search knowledge by semantic query |
| `learn(transcript_path, session_id)` | Extract knowledge from transcript (requires LLM) |
| `store(chunks, session_id)` | Save pre-extracted chunks directly (no LLM — used by `claude -p` subprocess) |
| `profile()` | Knowledge statistics |
| `digest()` | Duplicate detection + stale analysis |
| `memory(action, id?)` | promote/demote/delete/crystallize |
| `ingest(path)` | Extract knowledge from markdown/text files |

## Configuration

Config file: `.distill/config.json` (project) or `~/.distill/config.json` (global).
Config priority: project > workspace > global > defaults. All fields optional (zero-config).

```json
{
  "extraction_model": "claude-haiku-4-5-20251001",
  "crystallize_model": "claude-sonnet-4-5-20250929",
  "max_transcript_chars": 100000,
  "auto_crystallize_threshold": 0,
  "sources": {
    "transcripts": true,
    "rules": true,
    "skills": true,
    "agents": false,
    "dirs": ["docs/", "wiki/"]
  },
  "outputs": {
    "rules": { "enabled": true, "budget_max_files": 5, "confidence_threshold": 0.7, "split_threshold_tokens": 500 },
    "skills": { "enabled": true, "confidence_threshold": 0.6 },
    "agents": { "enabled": false, "min_skills_to_merge": 3 }
  }
}
```

## Scope

| Scope | Path |
|-------|------|
| global | `~/.distill/knowledge/` |
| workspace | `<git-root>/.distill/knowledge/` |
| project | `.distill/knowledge/` |

## Docs

- [Architecture](docs/architecture.md) — system diagrams (Mermaid), layer details
- [Configuration](docs/configuration.md) — MCP registration, config.json, hooks setup
- [Development](docs/development.md) — project structure, testing, conventions

## Rules

- [Contribution](.claude/rules/contribution.md)
