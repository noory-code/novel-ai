---
name: solera-plan
user-invocable: true
description: Turn a goal into a Solera Story decomposed into small, individually gated Actions.
metadata:
  version: "6.0.0"
  category: planning
  type: unit
  style: procedure
  triggers: [solera plan, plan the work, break down the goal, decompose into actions]
  uses: []
---

# solera-plan

Turn a goal into a Story and decompose it into Actions. The split is your
judgement; the files are written by the CLI so they always stay valid.

## When to use

When the user states a goal and wants it planned into executable work before any
building starts.

## Procedure

1. Create the Story:

   ```bash
   uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" plan "<goal>"
   ```

   It prints the Story id (e.g. `STORY-001`).

2. Decompose into Actions. For each chunk, decide:
   - **goal** — one chunk you can finish in a single context.
   - **gate** — a command that exits 0 only when the chunk is genuinely done
     (a test, a build, a file/So content check). The gate is deterministic and
     shell-independent; prefer `pytest ...`, `python -c "..."`, a linter, etc.

   ```bash
   uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
     add STORY-001 "<action goal>" --gate "<verification command>"
   ```

   Repeat in execution order. Each `add` prints the Action id.

## Rules for good Actions

- One context each. If a chunk needs more, split it further.
- Every Action has a gate. No gate means it cannot be auto-verified.
- The gate checks the *outcome*, not the steps (e.g. "tests pass", not "ran
  pytest"). Anyone re-running the gate later must get the same verdict.

When the plan is ready, hand off to **solera-run**.
