---
name: digest
description: Analyze knowledge for duplicates and stale entries.
metadata:
  version: "1.0.0"
  category: maintenance
  type: unit
  style: tool
  triggers: [distill digest, find duplicates, stale knowledge, clean up knowledge, distill cleanup]
  uses: [mcp__distill__digest]
---

# /distill:digest

Analyze accumulated knowledge for duplicate and stale entries.

## Usage

```
/distill:digest
```

## MCP Tool

Call `mcp__distill__digest` — no parameters required.

## Output includes

- **Duplicate pairs**: entries with >70% word overlap
- **Stale entries**: low confidence (<0.5) and never accessed (access_count=0)
- **Entry count**: total per scope

## Follow-up

After reviewing duplicates, use `/distill:memory` to delete unwanted entries:
```
memory(action="delete", id="<chunk-id>")
```
