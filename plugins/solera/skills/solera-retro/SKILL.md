---
name: solera-retro
user-invocable: true
description: After a Solera WorkItem finishes, record what the design lacked so a human can fold it back.
metadata:
  version: "7.8.0"
  category: feedback
  type: unit
  style: procedure
  triggers: [solera retro, retrospective, what did we learn, post-mortem the story]
  uses: []
---

# solera-retro

Written **after** a WorkItem is done. A retrospective is the post-hoc signal: what
the design or plan lacked, captured while it is fresh, for a human to fold back
into the design (in Novel, when connected).

## When to use

Right after `next` reports `(nothing open)`, or when a container has rolled up to done.

## Procedure

Call Solera MCP `write_retrospective` with the current workspace as
`project_root`, the WorkItem id as `item`, and the concrete learning as `body`.

Optionally tag the ids it is about (repeatable; only meaningful when Novel is
connected — omit in standalone):

Pass stable design identifiers in the optional `about` list.

This writes `retros/STORY-001.md` (it attaches to any item id).

## What to write

- Where the plan was wrong-sized (leaves too big or too small).
- A gap the design did not cover that only surfaced during the work.
- A gate that passed but should have checked more.

Keep it concrete. This is a sensor reading, not a summary of what happened.
