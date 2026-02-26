# Distill

> Automatically distill reusable knowledge from your Claude Code conversations.

Distill is an MCP (Model Context Protocol) server that analyzes your AI coding conversations and extracts patterns, preferences, decisions, and lessons learned — so Claude remembers what matters across sessions.

**No API key needed.** Distill uses MCP Sampling, which routes through your existing Claude subscription.

## How It Works

When you work with Claude Code, valuable knowledge emerges through conversation — corrections you make, patterns you establish, architectural decisions you commit to. Distill captures these automatically.

**Extraction signals** (ordered by confidence):

1. **Decision signals** — Any moment a direction was set: corrections (either party), convergence after discussion, or selection among alternatives
2. **Explicit preferences** — "always use X", "I prefer Y"
3. **Error resolutions** — An error occurred, root cause found, solution applied
4. **Accumulated patterns** — Repeated code/architecture patterns or consistent decision directions

Each extracted piece of knowledge is classified by type, scope, and confidence, then stored locally in SQLite with full-text search.

## Installation

### 1. Clone and install

```bash
git clone https://github.com/noory-code/noory-ai.git
cd noory-ai/distill
uv sync
```

### 2. Register as Claude Code plugin (recommended)

```
/install-plugin /absolute/path/to/noory-ai/distill
```

This registers the MCP server, skills, and hooks automatically via `plugin.json`. Replace `/absolute/path/to/noory-ai/distill` with the actual absolute path to the distill directory on your system.

### 3. Or register as standalone MCP server

Add a `.mcp.json` file in your project root:

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

Restart Claude Code after updating `.mcp.json`.

### 4. Enable automatic extraction (optional)

When installed as a plugin, hooks are registered automatically (PreCompact, SessionEnd). See [docs/configuration.md](docs/configuration.md) for the full hooks configuration.

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

**Ingest your documentation:**
```
ingest("docs/")
```

**Search for knowledge:**
```
recall("how to handle authentication in this project")
```

**View your knowledge profile:**
```
profile()
```

**Manage knowledge scope:**
```
memory("promote", "chunk-id")      # move one step up (project → workspace → global)
memory("demote", "chunk-id")       # move one step down (global → workspace → project)
memory("delete", "chunk-id")       # remove entry
memory("crystallize")              # consolidate into rule files
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

Knowledge is stored in three scopes:

| Scope | Path | Purpose |
|-------|------|---------|
| `global` | `~/.distill/knowledge/` | Language/framework patterns (portable across projects) |
| `workspace` | `<git-root>/.distill/knowledge/` | Shared monorepo conventions (between packages) |
| `project` | `.distill/knowledge/` | Project-specific conventions and decisions |

All available scopes are searched simultaneously by `recall`. Use `memory("promote", id)` to move knowledge one step up (project → workspace → global), or `memory("demote", id)` to move it down.

## Configuration

See [docs/configuration.md](docs/configuration.md) for detailed setup instructions.

## Architecture

See [docs/architecture.md](docs/architecture.md) for technical details and system diagrams.

## Contributing

See [docs/development.md](docs/development.md) for development setup and guidelines.

## License

[MIT](LICENSE)
