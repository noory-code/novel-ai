---
name: solera-repin
user-invocable: true
description: Compare adjacent imported service releases and surface work affected by service, shared-project, or refs changes.
metadata:
  version: "7.8.0"
  category: execution
  type: unit
  style: procedure
  triggers: [solera repin, repin after republish, plot republished, design changed, stale items]
  uses: [solera-run]
---

# solera-repin

When Novel republishes a service (`vS+1`), service-owned elements, referenced
project elements, or the service's refs may have changed. `repin` compares the
old and new imported releases and classifies affected Solera work items as
stale reopen candidates or escalations that require a human decision.

## When to use

Novel has published a new version of a service and you want to find which already-
planned (or already-done) items no longer match the current design.

## Procedure

### 1. Import the new release

Call `import_spec` with the new release path and a distinct `label`.

Use a distinct label from the previous import (e.g. `auth-v2`).

### 2. Propose the diff

Call `propose_spec_repin` with `old_label` and `new_label`. The labels must be
adjacent releases of the same service. If releases were skipped, import every
intervening release and compare them one step at a time.

The proposal reports a `proposal_id`, the service diff, shared-project diff,
whether refs changed, the stale and escalation lists, and per-item reasons. No
files are written. Show the complete proposal, including its ID, to the human.

### 3. Apply (human approval)

After the human explicitly approves the proposed reopens, call
`apply_spec_repin` with the same labels and the exact approved `proposal_id`.
The apply call recalculates the proposal. If the manifests, realizing work, or
classification changed, the ID does not match: no files are written. Propose
again, show the new proposal to the human, and wait for approval of its new ID.

Stale `done` items reopen to `todo`. Ancestor containers whose rollup broke also
reopen (rollup-invariant repair). The items are now back in the execution queue.

### 4. Continue

Hand off to **solera-run** to re-execute the reopened leaves against the updated
design.

## Rules

- Always propose before applying. Show the stale and escalation lists with the
  `proposal_id` to the human. Apply only the exact ID they approved.
- Re-pin reads both `service/manifest.json` and `project/manifest.json` under
  each label. A changed project element affects service work only when either
  release's refs points to it. A refs-only change also affects service work.
- A work item escalates when it realizes a removed service or shared-project
  element. It also escalates when it already realizes a service element that is
  `added` in the new release, because that ID may have been deleted and
  reintroduced. Escalation takes precedence over stale.
- Other newly added service elements are work candidates, but re-pin does not
  create items. Plan them with `add_work_item(realizes=[...])` after review.

`accept` is required when creating an item without a gate: `children` rolls up finished children, `person` waits for that person's judgment, and agents never judge a person's result.
