---
name: recall
description: Search accumulated knowledge by semantic + keyword hybrid search.
metadata:
  version: "1.0.0"
  category: search
  type: unit
  style: tool
  triggers: [recall, search knowledge, find knowledge, distill recall, what do I know about]
  uses: [mcp__distill__recall]
---

# /distill:recall

Search your accumulated knowledge using hybrid semantic + keyword search.

## Usage

```
/distill:recall <query>
```

## MCP Tool

Call `mcp__distill__recall` with:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | *required* | Natural language search query |
| `scope` | string | None | Filter: `global`, `workspace`, or `project` |
| `knowledge_type` | string | None | Filter: `pattern`, `preference`, `decision`, `mistake`, `workaround` |
| `limit` | int | 5 | Max results (up to 20) |
| `min_confidence` | float | 0.0 | Minimum confidence threshold (0.0-1.0) |

## Examples

- "Recall how I handle authentication" → `recall(query="authentication")`
- "Search global patterns about testing" → `recall(query="testing", scope="global", knowledge_type="pattern")`
- "Find high-confidence decisions" → `recall(query="architecture", min_confidence=0.8)`

## Notes

- Results ranked by combined relevance (50% search score + 35% confidence + 15% access frequency)
- Searches across all scopes (global, workspace, project) unless filtered
