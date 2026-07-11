---
name: distill-memory
user-invocable: true
description: Promote, demote, or delete one Distill knowledge entry without requiring MCP Sampling.
metadata:
  version: "1.9.1"
  category: maintenance
  type: unit
  style: tool
  triggers: [distill memory, promote knowledge, demote knowledge, delete knowledge]
  uses: [mcp__distill__manage_entry]
---

# Distill entry management

Call Distill MCP `manage_entry` with an `action` of `promote`, `demote`, or
`delete` and the exact entry `id`.

| Action | Effect |
|---|---|
| `promote` | Move project to workspace, or workspace to global scope |
| `demote` | Move global to workspace, or workspace to project scope |
| `delete` | Remove the entry from metadata and vector storage |

Use `distill-digest` or `distill-recall` first when the user has not supplied an
exact id. Deletion is irreversible, so show the selected entry and obtain
confirmation immediately before calling `manage_entry(action="delete")`.
