# Novel

**The mindmap editor with every React Flow feature built in — plus an AI that reads the map with you.**

Multi-select, drag-to-connect, copy/paste, undo/redo, auto-layout, context menu, MiniMap, resize, color — nothing to turn on, everything works out of the box. Your sketches live as plain JSON under `.noory/novel/` in your project, and an MCP server exposes them to Claude Code so the AI can read, extend, and reshape your map.

Three senses of the name — **plot the graph**, **plot the story**, **plot the plan** — cover what the tool is for.

## Install (Claude Code)

```text
/plugin marketplace add noory-code/novel-ai
/plugin install mashbill@novel-ai
```

## Quick start

```bash
# Install dependencies
uv sync

# Run the combined MCP + HTTP server for a project
uv run python -m mashbill --project /path/to/project

# Open the canvas
open http://127.0.0.1:5190/?project_path=/path/to/project
```

Novel data is written to `{project}/.noory/novel/`. Legacy `.noory/plot/` and
`.plot/` roots are migrated when opened.

## Development

```bash
# Tests
uv run pytest

# Viewer
cd viewer && npm install && npm run dev
```

## Architecture

- `mashbill/` — Python MCP server + Starlette HTTP + watchdog watcher
- `viewer/` — React 18 + Vite 5 + React Flow 11 canvas
- `.claude-plugin/plugin.json` — Claude Code plugin manifest

Version **0.1.0** — initial release, no schema, single sketch canvas.
