---
name: solera-plan
user-invocable: true
description: Split a goal into Solera WorkItems as deep as their results need, choosing acceptance for each item.
metadata:
  version: "7.8.0"
  category: planning
  type: unit
  style: procedure
  triggers: [solera plan, plan the work, break down the goal, split into work items]
  uses: []
---

# solera-plan

Turn a goal into a tree of WorkItems, split as deep as its results need. Choose
how each result is accepted. The files are written by the CLI so they always
stay valid.

## When to use

When the user states a goal and wants it planned into executable work before any
building starts.

## Procedure

1. Create a root. `level` is a free label with no fixed names; choose a label
   that describes the item, without treating it as a depth or size:

   Call Solera MCP `plan_work` with `project_root` set to the current workspace,
   the exact `goal`, `level="work"`, and `accept="children"` when the root will
   roll up its children. For a result promised to the person, use
   `accept="person"` instead.

   It returns the id (e.g. `WORK-001`); the prefix comes from the free `level`
   label and carries no meaning.

2. Add a child only when its result is part of its parent's result. Work that
   only has to happen first is an `after` waiting link, not a child:

   Call `add_work_item` once per child, with `level="work"`. Choose `accept` per
   item: `gate` for a result an agent builds and a deterministic command judges
   (pass that command in `gate`); `children` for a result that rolls up its
   children (pass `accept="children"` without a gate); `person` for a result a
   person tries and accepts (pass `accept="person"` without a gate).

   Each call returns the new id. When one item must finish before another
   starts, pass the earlier ids in `after` (for example `after=["WORK-002"]`).
   A link may point at any item, across parents; a link on a container holds
   back everything under it. Items with no link between them may run in any
   order, so link only real prerequisites — do not chain every leaf. To add or
   change links on an existing item, call `set_work_item_after` with the full
   list (an empty list clears it). Solera rejects an unknown id or a link that
   could never be satisfied.

## Rules for good items

- **Order links are facts, not a schedule.** Add `after` only when the later
  item needs the earlier one done — it reads its output, builds on its code, or
  needs its decision.
- **A leaf is one context.** If a chunk needs more than one clean agent context,
  make it a container and split it into smaller leaves.
- **A gate judges a result an agent builds.** The gate is
  deterministic and shell-independent — prefer `pytest …`, `python -c "…"`, a
  linter, a build.
- **A person accepts results promised to them and choices only they can make.**
  Choosing a design, signing a contract, approving copy, or trying a promised
  result uses `accept="person"`. A person finishes it by checking it in the
  app, and no agent can (D-2026-10-02-D). Do not invent a gate for it or split
  it to make it gated.
- The gate checks the *outcome*, not the steps ("tests pass", not "ran pytest").
  Anyone re-running it later must get the same verdict.
- Some leaves are *decisions*, not builds (e.g. "choose the stack"). The person
  makes and accepts the choice; see **solera-decide**.

When the plan is ready, hand off to **solera-run**.

`accept` is required when creating an item without a gate: `children` rolls up finished children, `person` waits for that person's judgment, and agents never judge a person's result.
