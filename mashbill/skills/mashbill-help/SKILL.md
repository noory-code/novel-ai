---
name: mashbill-help
user-invocable: true
description: Explain what Novel is, how to open the canvas, and the available skills.
metadata:
  version: "0.1.0"
  category: meta
  type: unit
  style: guide
  triggers: [what is plot, plot help, plot get started, plot open, how to use plot]
  uses: []
---

# Novel Help (v0.1)

> A full-featured mindmap editor built on React Flow, with an AI collaborator that reads the same map.

## What Novel is

Novel stores sketches as plain JSON under `{project}/.plot/sketches/{id}.json`. Each sketch is a graph of nodes and edges — no schema, no required fields, draw what makes sense for the problem at hand. The viewer ships with every React Flow free feature wired:

- **Editing**: double-click canvas to add a node, click a label to rename, drag handles to connect nodes, double-click a node for the full editor (body / color / size).
- **Selection**: Shift-click or drag-rectangle to multi-select, Cmd/Ctrl+A to select everything.
- **Clipboard**: Cmd/Ctrl+C / V / D — copy/paste/duplicate selected nodes with their incident edges, fresh ids on paste.
- **History**: Cmd/Ctrl+Z and Shift+Cmd/Ctrl+Z — 50-entry undo/redo.
- **Navigation**: MiniMap, fit-view Controls, pan on drag, zoom on wheel, dotted Background.
- **Right-click**: context menus for nodes (duplicate/copy/color/delete), edges (toggle dashed/label/delete), and the pane (add-here/paste/auto-layout).
- **Auto-layout**: dagre-based LR arrangement; orphan nodes stay where you put them.

AI reads and writes the same sketches via the MCP server — if you need help organising, extending, or proposing connections, ask Claude directly.

## Opening the canvas

1. Run the server against your project: `uv run python -m mashbill` (inside `mashbill/`), or let the plugin's MCP wrapper start it automatically.
2. Open `http://127.0.0.1:5190/?project_path=/absolute/path/to/project` in a browser.
3. First visit in an empty project shows "No sketches yet" — press **New sketch** to create one.

The sidebar lets you switch sketches, rename them inline (pencil icon), or delete them.

## Skills in this plugin

- `/mashbill-help` (this skill) — overview + quick start.
- `/mashbill-new-sketch` — create a new sketch and open it.
- `/mashbill-read-sketch` — have Claude read the current sketch and describe what's drawn.

## Next up

- v0.2: VSCode extension bundle.
- v0.2+: richer AI skills (propose edges, summarise sub-graphs, align with a domain model).
