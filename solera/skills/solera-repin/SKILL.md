---
name: solera-repin
user-invocable: true
description: Diff two imported Novel releases and reopen work items whose realized features have changed.
metadata:
  version: "7.7.0"
  category: execution
  type: unit
  style: procedure
  triggers: [solera repin, repin after republish, plot republished, design changed, stale items]
  uses: [solera-run]
---

# solera-repin

When Novel republishes a service (`vS+1`), some features may have changed or been
removed. `repin` diffs the old and new imported releases and surfaces which
Solera work items have gone stale — items whose `realizes` target has changed or
disappeared.

## When to use

Novel has published a new version of a service and you want to find which already-
planned (or already-done) items no longer match the current design.

## Procedure

### 1. Import the new release

```bash
uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
  import .noory/novel/published/<service-slug>/vS<N+1>/ --label <new-label>
```

Use a distinct label from the previous import (e.g. `auth-v2`).

### 2. Propose the diff

```bash
uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
  repin <old-label> <new-label>
```

This prints a proposal — which items are stale and why (changed element hash,
removed element, or added element with no matching item). No files are written.
Review the list with the human before applying.

### 3. Apply (human approval)

If the human approves the proposed reopens:

```bash
uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" \
  repin --apply <old-label> <new-label>
```

Stale `done` items reopen to `todo`. Ancestor containers whose rollup broke also
reopen (rollup-invariant repair). The items are now back in the execution queue.

### 4. Continue

Hand off to **solera-run** to re-execute the reopened leaves against the updated
design.

## Rules

- Always propose before applying. Show the stale list to the human — they decide
  whether the change is significant enough to reopen work.
- The diff compares element hashes from `specs/{label}/manifest.json`. A hash
  change means the feature's UX flow or definition changed in Novel; a missing id
  means the feature was removed.
- `added` elements (features in the new release with no matching item) are
  flagged but not created — plan new items with `solera add --realizes <slug>`
  after the repin.
