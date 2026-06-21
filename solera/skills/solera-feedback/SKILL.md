---
name: solera-feedback
user-invocable: true
description: While blocked on a Solera Action, record a neutral note for a human and stop.
metadata:
  version: "6.0.0"
  category: feedback
  type: unit
  style: procedure
  triggers: [solera feedback, i am blocked, escalate, cannot pass the gate]
  uses: []
---

# solera-feedback

Written **while blocked**, mid-work. Feedback is the escalation channel: a
neutral note describing what is in the way, for a human to act on. Writing it is
how you stop correctly instead of forcing a gate.

## When to use

You are on an Action and cannot make its gate pass for a reason you should not
decide alone: the goal is ambiguous, the design conflicts, a required tool or
permission is missing.

## Procedure

```bash
uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
  feedback FB-001 "<what is blocking, and what decision or input you need>"
```

Optionally tag the ids it is about (repeatable; omit in standalone):

```bash
  ... feedback FB-001 "<text>" --about feature/login
```

This writes `feedback/FB-001.md`. Then **stop** and tell the user you are
blocked — do not work around the gate.

## What to write

- The specific blocker, not a vague "this is hard".
- The decision or input you need from the human to proceed.
- What you already tried, so the human does not repeat it.
