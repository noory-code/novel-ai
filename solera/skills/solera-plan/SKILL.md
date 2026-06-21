---
name: solera-plan
user-invocable: true
description: Turn a goal into a Solera WorkItem tree decomposed down to small, individually gated leaves.
metadata:
  version: "6.0.0"
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

   ```bash
   uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
     plan "<goal>" --level initiative
   ```

   It prints the id (e.g. `INIT-001`).

2. Decompose downward by adding children under a parent. Containers (no gate)
   group; leaves (with a gate) are the work:

   ```bash
   # a grouping container under the root
   uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
     add INIT-001 "<epic goal>" --level epic
   # a gated leaf under that container
   uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
     add EPIC-001 "<action goal>" --level action --gate "<verification command>"
   ```

   Add leaves in execution order. Each `add` prints the new id.

## Rules for good items

- **A leaf is one context.** If a chunk needs more than one clean agent context,
  make it a container and split it into smaller leaves.
- **Every leaf has a gate; containers never do.** The gate is deterministic and
  shell-independent — prefer `pytest …`, `python -c "…"`, a linter, a build.
- The gate checks the *outcome*, not the steps ("tests pass", not "ran pytest").
  Anyone re-running it later must get the same verdict.
- Some leaves are *decisions*, not builds (e.g. "choose the stack"). Their gate
  is "a decision is recorded"; they escalate to a human via **solera-feedback**.

When the plan is ready, hand off to **solera-run**.
