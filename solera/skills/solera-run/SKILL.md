---
name: solera-run
user-invocable: true
description: Execute a planned Solera Story one Action at a time, verifying each through its gate.
metadata:
  version: "6.0.0"
  category: execution
  type: unit
  style: procedure
  triggers: [solera run, run the plan, do the next action, execute the story]
  uses: [solera-feedback]
---

# solera-run

Execute the plan one Action at a time. You do the building; Solera orders the
work and runs each gate.

## Procedure (repeat until nothing is open)

1. Take the next Action:

   ```bash
   uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" next
   ```

   - Prints `(nothing open)` -> the Story is complete. Stop. Consider
     **solera-retro**.
   - Otherwise prints the instruction: the Action id, its goal, and the gate.

2. **Build it.** Do the work the goal describes, in the project. Do not run the
   gate yourself — just make it pass.

3. Verify:

   ```bash
   uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" complete
   ```

   - `PASS` -> the Action is `done`. Go back to step 1.
   - `FAIL` -> the Action stays `doing`. Read the printed gate output, fix the
     work, and re-run `complete`.

## When to stop and escalate

If you cannot make the gate pass — the goal is ambiguous, a tool is missing, the
design is wrong — do **not** force it. Write a feedback note with
**solera-feedback** and stop for a human. A failed gate must never be worked
around.

## Check state any time

```bash
uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" status
```

Prints the current pointer and any integrity problems (exit non-zero if any).
