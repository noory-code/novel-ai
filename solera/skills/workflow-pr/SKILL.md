---
name: workflow-pr
description: Upon Epic completion, creates a PR to the parent branch, reviews it, and merges.
metadata:
  version: "2.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [create PR, make PR, Epic merge, merge to parent branch]
  uses: []
---

# Workflow PR

> Upon Epic completion, creates a PR to the parent branch, reviews it, and merges.

## Prerequisites

- All Stories in the Epic have been squash merged (status ✅)
- Build and tests pass on the Epic branch

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **epic_branch** | Y | PR source branch | epic-auth |
| **target_branch** | Y | Merge target branch | dev, main |

## Output

| Step | Output | Description |
|------|--------|-------------|
| Create PR | GitHub PR (URL) | One PR per Epic |
| Merge | Merge commit | squash merge |

## Procedure

1. **Prepare PR**
   - [ ] Confirm all Stories in the Epic are ✅
   - [ ] Confirm build and tests pass
   - [ ] Confirm no conflicts against target_branch (rebase if conflicts exist)

2. **Create PR**
   - [ ] `gh pr create --base {target_branch} --head {epic_branch}`
   - [ ] PR title: `[Epic] {epic_name}: {one-line summary}`
   - [ ] PR body: Stories list, key changes, test results — ref: [assets/pr-template.md](assets/pr-template.md)

3. **Handle review**
   - [ ] Check review comments
   - [ ] Add commits to the Epic branch for any fixes
   - [ ] Re-confirm CI passes

4. **Merge**
   - [ ] Execute the PR squash merge
   - [ ] Confirm the source branch is deleted

## PR Title Format

```
[Epic] {epic-name}: {summary}
```

## References

| File | Content |
|------|---------|
| [assets/pr-template.md](assets/pr-template.md) | PR body template |
| [self-verification.md](assets/self-verification.md) | Automated skill definition verification TCs (7 cases) |

## Completion Checklist

- [ ] PR created
- [ ] CI passed
- [ ] Review complete
- [ ] Merge complete
- [ ] Source branch deleted
