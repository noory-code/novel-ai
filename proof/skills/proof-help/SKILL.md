---
name: proof-help
user-invocable: true
description: Explain what Proof is — an append-only decision log — and its commands.
metadata:
  version: "0.3.0"
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

## Commands

```bash
uv run --directory "${CLAUDE_PLUGIN_ROOT}" proof --root "$PWD" <command>
```

| Command | What it does |
|---|---|
| `record "<title>" [--status …] [--about …] [--supersedes …] --body "…"` | Append a decision. See **proof-record**. |
| `list` | Every decision, with status. |
| `in-force [--about <id>]` | Decisions still standing (accepted, not superseded). |
| `check --about <id>` | Gate: exit 0 if an in-force decision tags the id, else 1. |
| `show <id>` | Print one decision in full. |

## Rules

- A decision is **in force** when it is `accepted` and no accepted decision
  supersedes it — this is *derived*, never stored.
- Never edit a recorded decision. To change course, `record` a new one with
  `--supersedes <old-id>`.
- `--about` links a decision to what it governs (a work-item, a topic slug, a
  feature) so a gate or query can find it.
