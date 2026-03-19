---
name: solera-create-pr
user-invocable: true
description: Wrap up an Epic by opening a PR, reviewing the diff, and merging cleanly into the parent branch.
metadata:
  version: "4.0.0"
  category: workflow
  type: unit
  style: procedural
  triggers: [create a pull request, open a PR, merge the Epic, merge into parent branch, submit for review]
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
| **epic_branch** | Y | PR source branch | epics/auth |
| **target_branch** | N | Merge target branch (overrides config) | dev, main |

## Target Branch Resolution

Resolve the target branch using this priority order:

1. If `target_branch` parameter is explicitly provided: use it
2. If `.claude/rules/solera-workflow.md` contains an uncommented `default_pr_base:` value under `## Project Config`: use that value
3. If neither exists: ask the user "Which branch should this PR target?" and wait for a response before proceeding

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create PR | GitHub PR (URL) | One PR per Epic | Final |
| Merge | Merge commit | squash merge | Final |

## Procedure

1. **Prepare PR**
   - [ ] Confirm all Stories in the Epic are ✅
   - [ ] **Artifact promotion check**: Scan `{goal_path}/artifacts/` for Epic-level directories: `use-case`, `concept`, `erd`, `dto`, `api-spec`
     - If any of these directories contain at least one file: **BLOCK** — list the un-promoted files and output: "Run `solera-publish-artifacts` before creating the PR. Epic-level artifacts must be promoted to `published/` first."
     - If none of these directories contain files (or directories do not exist): proceed
   - [ ] **Resolve target_branch** per Target Branch Resolution above
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
| [self-verification.md](assets/self-verification.md) | Automated skill definition verification TCs (10 cases) |

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| Stories incomplete | Some Stories in the Epic are not ✅ | Display incomplete Story list, request completion | Skill halted, resume after all Stories complete |
| Artifacts not promoted | Epic-level files exist in `{goal_path}/artifacts/` (use-case, concept, erd, dto, api-spec) | Display un-promoted file list, instruct to run `solera-publish-artifacts` | Skill halted, resume after promotion complete |
| target_branch unknown | Parameter not provided, no config, user unresponsive | Re-ask user for target branch | Wait at Prepare PR step, proceed after response |
| Build/test failed | Build or test failure on Epic branch | Display error message, request fix | Skill halted, resume after fix |
| Branch conflict | Conflict detected against target_branch | Display conflicting file list, request rebase and retry | Prepare step halted, resume after rebase |
| gh CLI not installed | `gh` command missing | Display GitHub CLI installation instructions | Skill halted, resume after installation |
| PR creation failed | gh pr create error (permissions, auth, etc.) | Display gh error message, request auth verification | Create PR step halted, retry after auth |
| CI failed | PR CI check failed | Display failed CI jobs, request fix | Handle review step halted, re-verify after fix commit |
| Merge failed | Squash merge error | Display error message, request manual merge | Merge step halted, confirm after manual resolution |
| Branch deletion failed | Source branch deletion failed | Display warning message, request manual deletion | Skill complete (deletion is not required), recommend manual cleanup |

## Completion Checklist

- [ ] Artifact promotion verified (no Epic-level artifacts in artifacts/)
- [ ] target_branch resolved
- [ ] PR created
- [ ] CI passed
- [ ] Review complete
- [ ] Merge complete
- [ ] Source branch deleted
