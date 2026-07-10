---
name: proof-help
user-invocable: true
description: Explain what Proof is — an append-only decision log — and its commands.
metadata:
  version: "0.5.0"
  category: meta
  type: unit
  style: guide
  triggers: [what is proof, proof help, decision log, how to use proof, record a decision]
  uses: [proof-record]
---

# Proof

Proof is an **append-only decision log**. Significant choices — a tech stack, an
architecture, a convention — are recorded once and **never edited**. To change a
decision you record a new one that **supersedes** it, so the history (what was
decided, why, and what it replaced) is preserved.

Proof is a **shared substrate**: other tools (mashbill, Solera) point at decisions by
**id, by value** — they never import it. It runs standalone over plain files under
`.noory/proof/` in the project directory.

## MCP tools

Pass the current workspace as `project_root` to every tool.

| Tool | What it does |
|---|---|
| `record_decision` | Append a decision. See **proof-record**. |
| `list_decisions` | Return every decision, including superseded entries. |
| `decisions_in_force` | Return accepted decisions that have not been superseded. |
| `check_decision` | Report whether an in-force decision tags an `about` id. |
| `show_decision` | Read one decision by stable id. |

## Rules

- A decision is **in force** when it is `accepted` and no accepted decision
  supersedes it — this is *derived*, never stored.
- Never edit a recorded decision. To change course, call `record_decision` with
  `supersedes` set to the old id.
- `about` links a decision to what it governs (a work-item, a topic slug, a
  feature) so a gate or query can find it.
