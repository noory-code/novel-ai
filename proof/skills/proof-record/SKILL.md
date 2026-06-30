---
name: proof-record
user-invocable: true
description: Record a well-formed decision in proof — context, decision, alternatives, consequences.
metadata:
  version: "0.3.0"
  category: decision
  type: unit
  style: procedure
  triggers: [proof record, record a decision, log this decision, write an ADR]
  uses: []
---

# proof-record

Append a decision to the log. A good decision entry is short but complete: a
later reader (or agent) should understand not just *what* was chosen but *why*,
and what was rejected.

## When to use

A significant choice has been made — a tech stack, an architecture, a convention —
and it should govern future work. For a choice the **human** owns, record it only
after they have decided (see Solera's `solera-decide`).

## Procedure

```bash
uv run --directory "${CLAUDE_PLUGIN_ROOT}" proof --root "$PWD" \
  record "Use Postgres for the primary store" \
  --status accepted \
  --about auth-stack \
  --body "$(cat <<'EOF'
## Context
Why a decision was needed.

## Decision
What we chose, stated plainly.

## Alternatives
- Option B — rejected because ...
- Option C — rejected because ...

## Consequences
- What this now constrains or requires downstream.
EOF
)"
```

It prints the new id (e.g. `PROOF-001`).

## Fields

- **status** — `accepted` (a human chose it) or `proposed` (a drafted option not
  yet chosen). Only `accepted` decisions count as in force.
- **--about** — id(s) this decision governs (a work-item, a topic slug like
  `auth-stack`, a feature). Lets gates and queries find it.
- **--supersedes `<id>`** — when this replaces an earlier decision. The old one
  stays in the log; it just stops being in force.

## Rules

- **Never edit** an existing decision. To change course, record a new one with
  `--supersedes`.
- Don't record an `accepted` decision on a human's behalf when the choice is
  theirs to make — surface the options and let them decide first.
- Keep the body concrete: the alternatives and consequences are the parts a
  future reader needs most.
