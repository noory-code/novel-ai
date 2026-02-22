# Configuration

## MCP Server Registration

Add to `~/.claude/mcp.json`:

```json
{
  "mcpServers": {
    "distill": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/distill", "run", "python", "-m", "distill"]
    }
  }
}
```

Restart Claude Code after updating `mcp.json`.

> **No API key needed.** MCP tools use MCP Sampling (`ctx.sample()`) — routes through your existing Claude subscription. Hooks use `claude -p` subprocess for automatic extraction.

## Config File

Config file: `.distill/config.json` (project or workspace) or `~/.distill/config.json` (global).
Priority: project > workspace > global. All fields are optional — Distill works with zero configuration.

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
    "rules": {
      "enabled": true,
      "budget_max_files": 5,
      "confidence_threshold": 0.7,
      "split_threshold_tokens": 500
    },
    "skills": {
      "enabled": true,
      "confidence_threshold": 0.6
    },
    "agents": {
      "enabled": false,
      "min_skills_to_merge": 3
    }
  }
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `extraction_model` | `claude-haiku-4-5-20251001` | Model hint for knowledge extraction (advisory — client decides) |
| `crystallize_model` | `claude-sonnet-4-5-20250929` | Model hint for crystallize (rule generation) |
| `max_transcript_chars` | `100000` | Max transcript size before truncation (keeps recent turns) |
| `auto_crystallize_threshold` | `0` (disabled) | Automatically crystallize after N new chunks since last crystallize |
| `sources.dirs` | `[]` | Directories to ingest on `init()` or manually via `ingest(path)` |
| `outputs.rules.budget_max_files` | `5` | Max number of distill rule files (context budget) |
| `outputs.rules.split_threshold_tokens` | `500` | Split rule file when topic exceeds this token size |
| `outputs.agents.enabled` | `false` | Generate agent files when 3+ related skills cluster |

### Per-Module Model Selection

Distill uses different models for different pipeline stages:

- **Extraction** (Haiku): Runs frequently on every `learn` or `ingest` call. Optimized for speed and cost.
- **Crystallize** (Sonnet): Runs infrequently when consolidating rules. Optimized for quality.

Model hints are advisory — they're passed via `model_preferences.hints` in the MCP Sampling request. The client (Claude Code) decides which model actually runs.

## Hooks (Automatic Extraction)

Hooks enable automatic knowledge extraction across Claude Code sessions.

| Event | When | Hook Script | Purpose |
|-------|------|-------------|---------|
| `PreCompact` | Context window about to compress | `distill_hook.py` | Extract before history is lost |
| `SessionEnd` | Session ends | `distill_hook.py` | Final extraction pass |

### How Hooks Work

At session end, `distill_hook.py` extracts knowledge via `claude -p` subprocess:

1. Loads `extraction_model` from config (default: `claude-haiku-4-5-20251001`)
2. Runs `claude -p --model <model>` → Claude reads transcript + calls `mcp__distill__store()`

### Setup

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreCompact": [
      {
        "type": "command",
        "command": "uv --directory /absolute/path/to/distill run python -m distill.hooks.distill_hook"
      }
    ],
    "SessionEnd": [
      {
        "type": "command",
        "command": "uv --directory /absolute/path/to/distill run python -m distill.hooks.distill_hook"
      }
    ]
  }
}
```

Update the paths to point to your Distill installation directory.

### Hook Input (PreCompact/SessionEnd)

Hooks receive JSON via stdin from Claude Code:

```json
{
  "session_id": "abc-123",
  "transcript_path": "/path/to/session.jsonl",
  "cwd": "/current/project/path",
  "hook_event_name": "PreCompact"
}
```


## Scope Directories

| Scope | Path | Created Automatically |
|-------|------|:---:|
| Global | `~/.distill/knowledge/` | Yes |
| Workspace | `<git-root>/.distill/knowledge/` | Yes |
| Project | `<project-root>/.distill/knowledge/` | Yes |

**Project root detection** walks up from CWD looking for these markers:
- `pyproject.toml`
- `pubspec.yaml`
- `package.json`
- `CLAUDE.md`

**Workspace root detection** walks up from CWD looking for a `.git/` directory (monorepo root).

In a single-repo setup (`.git/` and project marker at same path), only the project and global scopes are used.
In a monorepo, workspace scope stores shared conventions between packages.

**Config priority:** project `.distill/config.json` → workspace `.distill/config.json` → global `~/.distill/config.json` → defaults.

Add `.distill/` to your project's `.gitignore` to avoid committing knowledge databases.
