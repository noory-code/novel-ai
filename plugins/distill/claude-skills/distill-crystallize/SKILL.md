---
name: distill-crystallize
user-invocable: true
description: Use Claude MCP Sampling to consolidate stored Distill knowledge into Claude rules and skills.
metadata:
  version: "1.9.0"
  category: maintenance
  type: unit
  style: tool
  triggers: [distill crystallize, crystallize rules, generate distill rules]
  uses: [mcp__distill__memory]
---

# Crystallize Distill knowledge

This Claude Code-only workflow requires MCP Sampling. Call Distill MCP `memory`
with `action="crystallize"` and no id. Present the report of created, updated,
removed, downgraded, and conflicting rules to the user. Never conceal conflicts
with user-authored rules or overwrite them manually.
