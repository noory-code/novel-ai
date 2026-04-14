---
name: solera-create-pr
user-invocable: true
description: Open a PR for a completed Story, handle the review cycle, and squash-merge into trunk.
metadata:
  version: "5.0.0"
  category: workflow
  type: unit
  style: procedural
  triggers: [create a pull request, open a PR, merge the Story, submit for review, PR this story]
  uses: []
---

# Create PR (v3)

> Upon Story completion, creates a PR from the Story branch to trunk, handles the review cycle, and squash-merges.

In v3 the PR unit is the **Story**, not the Epic (Epic was removed). Each Story branch (`story/{story_id}-{story_name}`) becomes one PR. Action Item commits collapse into a single squash commit on trunk.

## Prerequisites

- The Story is on its own branch (`story/{story_id}-{story_name}`).
- All Action Items in the Story are ✅ (verified by reading `_story.md`'s Action Items table).
- Story Wrap-up has completed — RETROSPECTIVE.md exists with the required Concept Contribution Summary; Current Shape updates for every contributed Concept have been approved.
- Build and tests pass on the Story branch.

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **story_branch** | Y | PR source branch | `story/US-001-google-login` |
| **target_branch** | N | Merge target branch (overrides config) | `dev`, `main` |

## Target Branch Resolution

Priority order:

1. If `target_branch` parameter is explicitly provided: use it.
2. If `.claude/rules/solera-workflow.md` has an uncommented `default_pr_base:` value under `## Project Config`: use that.
3. Otherwise: ask the user "Which branch should this PR target?" and wait for a response.

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create PR | GitHub PR (URL) | One PR per Story | Final |
| Merge | Squash merge commit on trunk | — | Final |
| Cleanup | Source Story branch deleted | — | Final |

## Procedure

### 1. Prepare PR

- [ ] Read `{story_path}/_story.md`:
  - Extract `story_id`, `story_name`, `contributes_to`, `belongs_to` (if set), `status`.
  - Confirm `status: ✅ Complete`.
  - Extract `contributes_to[0]` as `primary_concept` (used in PR title).
- [ ] Read the Action Items table — confirm every row has status ✅ and a commit hash.
- [ ] Confirm RETROSPECTIVE.md exists and includes the **Concept Contribution Summary** section (`grep -q "## Concept Contribution Summary" RETROSPECTIVE.md`).
- [ ] For each `contributes_to` concept: confirm `concepts/{id}.md`'s `# Contributions` table has a row referencing this Story (evidence that Wrap-up's Current Shape update was applied).
- [ ] **Resolve target_branch** per Target Branch Resolution above.
- [ ] Confirm build and tests pass (run the project's test command — specified in `team-process.md` if defined).
- [ ] Confirm no conflicts against target_branch. If conflicts exist, halt and instruct the user to rebase:
  ```bash
  git checkout story/{story_id}-{story_name}
  git rebase {target_branch}
  ```

### 2. Create PR

- [ ] PR title: `[{primary_concept}][{story_id}] {story_name}`
- [ ] If the Story's `contributes_to` has multiple entries, prepend a body line: `Also contributes to: {other_concept_ids}`.
- [ ] PR body: filled from [assets/pr-template.md](assets/pr-template.md).
- [ ] Run:
  ```bash
  gh pr create \
    --base {target_branch} \
    --head {story_branch} \
    --title "[{primary_concept}][{story_id}] {story_name}" \
    --body "$(cat <<'EOF'
  ...filled template...
  EOF
  )"
  ```
- [ ] Record the returned PR URL.

### 3. Handle review

- [ ] Monitor the PR for review comments.
- [ ] For each requested change: add a commit to the Story branch (not a force-push, a new commit). Commit format follows the standard v3 format:
  ```
  [{primary_concept}][{story_id}][review] address {reviewer} feedback

  - {specific change}
  ```
- [ ] Re-confirm CI passes.

### 4. Merge

- [ ] Execute squash merge:
  ```bash
  gh pr merge {pr_number} --squash
  ```
  The resulting squash commit preserves the Action Items list in its body (GitHub auto-fills from the PR body).
- [ ] Confirm the source Story branch is deleted (GitHub's squash-merge UI auto-deletes by default; `gh` respects that setting).
- [ ] If branch deletion failed, issue a warning but do not fail the skill — `git branch -d story/{story_id}-{story_name}` can be run manually.

## PR Title Format

```
[{primary_concept}][{story_id}] {story_name}
```

Examples:
```
[authentication][US-001] google-login
[liquor-search][TS-014] fts5-index-migration
```

This keeps `git log --grep="\[authentication\]"` searchable by Concept across many Stories.

## Human–AI Protocol

| AI does | AI does not |
|---------|-------------|
| Verify Wrap-up completion (RETRO + Concept updates) before opening PR | Open a PR for a Story whose Current Shape updates were never approved |
| Tag PR title with `primary_concept` and `story_id` | Invent a scope tag different from `contributes_to[0]` |
| Add review-response commits to the Story branch | Force-push or rewrite the Story's existing history |
| Squash-merge after CI passes | Bypass CI failures or `--no-verify` the merge |

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| Story not complete | `_story.md` status ≠ ✅ | Halt; instruct user to finish Wrap-up first | Skill halts |
| Action Items incomplete | Some ACTs still ⏳/🔄 | Halt; list incomplete IDs | Skill halts |
| No RETROSPECTIVE | File missing or Concept Contribution Summary absent | Halt; instruct to complete Wrap-up | Skill halts |
| Concept Contributions unrecorded | No row in `concepts/{id}.md` Contributions | Halt; Wrap-up's Current Shape update step was skipped | Skill halts |
| target_branch unknown | No param, no config, user unresponsive | Re-ask; wait | Pause |
| Build/test failed | Test run exit ≠ 0 | Halt; request fix | Skill halts |
| Branch conflict | Rebase needed | Halt; print rebase command | Skill halts |
| `gh` CLI not installed | `gh` command missing | Halt; print install instructions | Skill halts |
| PR creation failed | gh auth or permission error | Halt; print gh output | Skill halts |
| CI failed on PR | Workflow failures | Halt review step; request fix | Pause |
| Merge failed | Squash merge error | Halt; request manual resolution | Skill halts |
| Branch deletion failed | After merge | Warn but continue; suggest `git branch -d` | Skill completes with warning |

## Completion Checklist

- [ ] Story status ✅, all ACTs ✅
- [ ] RETROSPECTIVE.md present with Concept Contribution Summary
- [ ] Each contributed Concept's `# Contributions` updated with this Story
- [ ] target_branch resolved
- [ ] PR created with `[{primary_concept}][{story_id}]` title
- [ ] CI passed
- [ ] Review cycle complete
- [ ] Squash merge executed
- [ ] Source Story branch deleted (or warning recorded)
