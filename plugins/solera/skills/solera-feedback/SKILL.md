---
name: solera-feedback
user-invocable: true
description: While blocked on a Solera leaf, record a neutral note for a human and stop.
metadata:
  version: "7.8.0"
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

You are on a leaf and cannot make its gate pass for a reason you should not
decide alone: the goal is ambiguous, the design conflicts, a required tool or
permission is missing.

## Procedure

Call Solera MCP `write_feedback` with the current workspace as `project_root`,
an explicit `feedback_id`, and the blocker plus required input as `body`.

Optionally tag the ids it is about (repeatable; omit in standalone):

Pass stable design identifiers in the optional `about` list.

This writes `feedback/FB-001.md`. Then **stop** and tell the user you are
blocked — do not work around the gate.

## What to write

- The specific blocker, not a vague "this is hard".
- The decision or input you need from the human to proceed.
- What you already tried, so the human does not repeat it.
