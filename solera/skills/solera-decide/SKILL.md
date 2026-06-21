---
name: solera-decide
user-invocable: true
description: Run a decision-type leaf — surface options, escalate to a human, and gate on the choice being recorded in cairn.
metadata:
  version: "7.1.0"
  category: planning
  type: unit
  style: procedure
  triggers: [solera decide, decide the stack, choose the technology, make a decision, decision item]
  uses: [solera-run, solera-feedback]
---

# solera-decide

Some leaves are not *build* work but *decide* work — choosing a tech stack, an
architecture, a convention. The choice is the **human's** to make ("use this!");
your job is to lay out the options. The decision is recorded in
[cairn](https://github.com/noory-code/noory-ai/tree/main/cairn), an append-only
decision log, and the leaf gates on that record existing.

## When to use

A WorkItem requires a decision that should not be made by the agent alone — it is
value-laden, it constrains downstream work, or the user owns it.

## Plan the decision leaf

Pick a short **topic slug** for the decision (e.g. `auth-stack`). Create a leaf
whose gate checks that a decision about that topic is in force:

```bash
uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
  add EPIC-001 "Decide the auth stack" --level action \
  --gate 'cairn --root "$PWD" check --about auth-stack'
```

(The gate references the *topic*, not the leaf's own id, so it can be set at plan
time. `cairn` must be installed / on PATH.)

## Run it

1. `next` hands you the decision leaf. **Do not decide.** Do a spike: research the
   options and lay out, for the human, the **alternatives, trade-offs, and a
   recommendation**. Stage your findings under the leaf's `artifacts/` if useful.

2. **Escalate to the human** with the options. If you are blocked from even
   presenting options, use **solera-feedback**.

3. The human chooses and records the decision in cairn:

   ```bash
   cairn --root "$PWD" record "Use Postgres" --status accepted \
     --about auth-stack \
     --body "$(cat <<'EOF'
   ## Context
   ...
   ## Decision
   Postgres.
   ## Alternatives
   - SQLite — rejected: ...
   ## Consequences
   - ...
   EOF
   )"
   ```

4. `complete` — the gate (`cairn check --about auth-stack`) now passes, the leaf
   is `done`, and its ancestors roll up.

## Rules

- **You surface; the human decides.** Never run `cairn record --status accepted`
  on your own behalf for a decision the human owns.
- The decision lives in **cairn**, not in Solera — append-only, and it governs
  every downstream item (anyone can `cairn in-force` to see what stands).
- To change a decision later, record a new one that supersedes it; never edit.
