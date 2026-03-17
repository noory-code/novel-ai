---
name: distill-profile
description: View knowledge statistics and hook status.
metadata:
  version: "1.0.0"
  category: stats
  type: unit
  style: tool
  triggers: [distill profile, knowledge stats, distill status, how much knowledge, distill statistics]
  uses: [mcp__distill__profile]
---

# /distill-profile

View accumulated knowledge statistics, environment summary, and last hook run status.

## Usage

```
/distill-profile
```

## MCP Tool

Call `mcp__distill__profile` with:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scope` | string | None | Filter: `global`, `workspace`, or `project`. None = all scopes |

## Output includes

- **Per-scope breakdown**: total entries, by type (pattern, preference, decision, etc.)
- **Most accessed**: top 3 most-recalled knowledge entries
- **Environment**: rule/skill/agent counts, budget usage
- **Last hook run**: timestamp, result, duration, errors (if any)
