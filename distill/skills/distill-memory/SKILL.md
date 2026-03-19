---
name: distill-memory
user-invocable: true
description: Manage knowledge entries — promote, demote, delete, or crystallize.
metadata:
  version: "1.0.0"
  category: maintenance
  type: unit
  style: tool
  triggers: [distill memory, promote knowledge, demote knowledge, delete knowledge, distill crystallize, crystallize rules]
  uses: [mcp__distill__memory]
---

# /distill-memory

Manage knowledge lifecycle: promote/demote scope, delete entries, or crystallize into rules.

## Usage

```
/distill-memory <action> [id]
```

## MCP Tool

Call `mcp__distill__memory` with:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action` | string | *required* | One of: `promote`, `demote`, `delete`, `crystallize` |
| `id` | string | None | Chunk ID (required for promote/demote/delete) |

## Actions

| Action | Description |
|--------|-------------|
| `promote` | Move entry to broader scope (project → workspace → global) |
| `demote` | Move entry to narrower scope (global → workspace → project) |
| `delete` | Remove entry permanently |
| `crystallize` | Consolidate all entries into `.claude/rules/distill-*.md` files |

## Typical Workflow

1. Run `/distill:digest` to find duplicates/stale entries
2. Delete unwanted: `memory(action="delete", id="<id>")`
3. Crystallize: `memory(action="crystallize")` to generate rule files
