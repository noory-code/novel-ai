---
name: solera-plan
user-invocable: true
description: Turn a goal into a Solera WorkItem tree decomposed down to small, individually gated leaves.
metadata:
  version: "7.8.0"
  category: planning
  type: unit
  style: procedure
  triggers: [solera plan, plan the work, break down the goal, decompose into actions]
  uses: []
---

# solera-plan

Turn a goal into a tree of WorkItems and decompose it down to gated leaves. The
split is your judgement; the files are written by the CLI so they always stay
valid.

## When to use

When the user states a goal and wants it planned into executable work before any
building starts.

## Procedure

1. Create a root. Pick its `--level` by how big the goal is — `initiative` for a
   large effort, `story` for a single feature (the default):

   Call Solera MCP `plan_work` with `project_root` set to the current workspace,
   the exact `goal`, and `level="initiative"`.

   It prints the id (e.g. `INIT-001`).

2. Decompose downward by adding children under a parent. Containers (no gate)
   group; leaves (with a gate) are the work:

   Call `add_work_item` once per child. Pass `gate=""` for a grouping
   container. Pass the exact deterministic verification command in `gate` for
   a leaf.

   Add leaves in execution order. Each `add` prints the new id.

## Rules for good items

- **A leaf is one context.** If a chunk needs more than one clean agent context,
  make it a container and split it into smaller leaves.
- **Every leaf has a gate; containers never do.** The gate is deterministic and
  shell-independent — prefer `pytest …`, `python -c "…"`, a linter, a build.
- The gate checks the *outcome*, not the steps ("tests pass", not "ran pytest").
  Anyone re-running it later must get the same verdict.
- Some leaves are *decisions*, not builds (e.g. "choose the stack"). Their gate
  is "a decision is recorded in proof"; the human makes the call. See
  **solera-decide**.

When the plan is ready, hand off to **solera-run**.
