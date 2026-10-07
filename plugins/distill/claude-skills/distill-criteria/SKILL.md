---
name: distill-criteria
user-invocable: true
description: Record, update, verify, and inspect sourced project decision criteria.
metadata:
  version: "1.10.0"
  category: memory
  type: unit
  style: tool
  triggers: [project criteria, decision criteria, current criteria, criterion history]
  uses:
    - mcp__distill__criteria_record
    - mcp__distill__criteria_revise
    - mcp__distill__criteria_revoke
    - mcp__distill__criteria_current
    - mcp__distill__criteria_check
    - mcp__distill__criteria_history
---

# Distill project criteria

Use these tools only when the user asks to record, change, revoke, or inspect a
project decision criterion. Do not extract criteria from conversation automatically.

- Record a criterion with its explicit `project`, conditions, confirmation state,
  and complete `origin` evidence.
- Revise or revoke only with a new user statement in `origin`, the current `base_version`,
  and a non-empty reason. An AI inference cannot replace a user's criterion.
- Use a unique `idempotency_key` for every intended write. Reuse that key only to
  retry the exact same request.
- Before relying on a returned reference, call `criteria_check` with the same
  project key. Apply only references whose status is `eligible_current`.
- Treat `unconfirmed`, `superseded`, `revoked`, `scope_mismatch`, and `unknown`
  references as ineligible.
- Use `criteria_history` when the user needs the source, revision reason, or older
  versions. General `recall` results are not current-criterion evidence.
