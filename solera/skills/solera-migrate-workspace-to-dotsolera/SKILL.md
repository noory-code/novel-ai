---
name: solera-migrate-workspace-to-dotsolera
user-invocable: true
description: One-shot, idempotent move of Solera v3 workspace data from `workspace/` (project root) to `.solera/` (dotfolder). Includes top-level `progress.md` and `HANDOFF.md`. BLOCKING confirmation; git as safety net; produces a single commit.
metadata:
  version: "1.0.0"
  category: meta
  type: unit
  style: procedural
  triggers: [migrate workspace to dotsolera, move workspace to .solera, hide solera workspace, dotfolder migration]
  uses: []
---

# Migrate `workspace/` → `.solera/` (Assisted)

> Solera v4 hides its working files inside a single dotfolder (`.solera/`) instead of a project-root `workspace/`. This skill does the move atomically and reversibly — one `git mv` per immediate child plus the two top-level state files, then one commit.

## Philosophy

This is a **one-shot transition skill**, not a work item. It runs once per project (or resumes once if interrupted). Like `solera-migrate-v2`, `solera-release`, and `solera-publish-artifacts`, its procedure lives entirely in this SKILL.md — there is no template-level Workflow for `solera-manage-workflow` to read.

Rules the skill follows:

- **Non-destructive.** Every move is `git mv`, preserving history. Nothing is deleted.
- **Blocking on judgment.** A single BLOCKING confirmation lists exactly what will move before any change happens.
- **Git as safety net.** All moves land in one commit so `git revert` undoes the entire migration with a single command.
- **Idempotent re-runs.** If re-invoked on an already-migrated project (`.solera/` exists, no `workspace/`), the skill detects state and exits with "already migrated" — no halt-with-error, no double-move.

### Why one commit, not multiple

`solera-migrate-v2` uses one commit per step because v2→v3 has seven independent decision points (skeleton, concepts, stories, milestone, release, cleanup) any of which the human may want to reset to. The `workspace/` → `.solera/` move has **no internal decision points** — it is a single atomic rename. Splitting it into multiple commits would leave the project in a broken intermediate state (some files moved, some not) where Solera skills could not find their data.

### Why no `## Workflow` section

Same reason as `solera-migrate-v2`: this is a one-shot transition skill that produces no ongoing lifecycle for `solera-manage-workflow` to drive.

## Prerequisites

- A git repository at `{project_path}` with a clean working tree (`git status --porcelain` is empty). If dirty, the skill refuses to start.
- A v3-shape workspace: `{project_path}/workspace/` exists with at least one immediate child (`identity/`, `concepts/`, `milestones/`, etc.).
- The Solera v4 plugin installed (this skill is part of it).

## Input

| Parameter | Required | Description | Example |
|---|---|---|---|
| **project_path** | Y | Project root containing `workspace/` | `/Users/me/banas` |

## Output

A single git commit moving:

| Source | Destination |
|---|---|
| `{project_path}/workspace/` (with all children) | `{project_path}/.solera/` |
| `{project_path}/progress.md` (if present at root) | `{project_path}/.solera/progress.md` |
| `{project_path}/HANDOFF.md` (if present at root) | `{project_path}/.solera/HANDOFF.md` |

`.gitignore` patched if any of the moved paths were listed.

## Procedure (5 steps, one BLOCKING gate)

### Step 1 — Preflight

- [ ] Run `git status --porcelain` at `{project_path}`. If any output → halt with: `"Working tree must be clean. Commit or stash your changes, then re-run."`
- [ ] Check `{project_path}/.solera/` does NOT exist:
  - If `.solera/` exists AND `workspace/` does NOT exist → migration is already complete. Exit with: `"Already migrated. .solera/ exists, workspace/ does not. Nothing to do."`
  - If both `.solera/` AND `workspace/` exist → halt with: `"Both .solera/ and workspace/ exist. Migration cannot proceed safely. Inspect manually and remove the wrong one before re-running."`
- [ ] Check `{project_path}/workspace/` exists with at least one entry. If absent or empty → halt with: `"No workspace/ to migrate at {project_path}."`
- [ ] Detect optional top-level state files:
  - `{project_path}/progress.md` — record presence
  - `{project_path}/HANDOFF.md` — record presence
- [ ] Inspect `{project_path}/.gitignore` for any of: `workspace/`, `progress.md`, `HANDOFF.md`. Record matches for Step 4.

### Step 2 — BLOCKING confirmation

- [ ] Build the move report:
  ```
  Migration plan for {project_path}:

  Workspace:
    workspace/  →  .solera/
      (immediate children: identity/, concepts/, milestones/, stories/, releases/, ...)

  Top-level state files:
    progress.md  →  .solera/progress.md     [present | absent]
    HANDOFF.md   →  .solera/HANDOFF.md      [present | absent]

  .gitignore patches:
    workspace/   →  .solera/                [if present in .gitignore]
    progress.md  →  .solera/progress.md     [if present in .gitignore]
    HANDOFF.md   →  .solera/HANDOFF.md      [if present in .gitignore]

  Mechanism: git mv (preserves git history). All in one commit.
  ```
- [ ] **BLOCKING**: present the report and ask `"Apply this migration? (yes/no)"`.
- [ ] On `no` → exit cleanly without modifying anything: `"Aborted. No changes made."`

### Step 3 — Move

- [ ] `git mv {project_path}/workspace {project_path}/.solera`. This single rename moves the directory and **all its contents** in one git operation. Do NOT iterate per child — git tracks the rename of the directory itself.
- [ ] If `progress.md` was detected at the project root: `git mv {project_path}/progress.md {project_path}/.solera/progress.md`.
- [ ] If `HANDOFF.md` was detected at the project root: `git mv {project_path}/HANDOFF.md {project_path}/.solera/HANDOFF.md`.

### Step 4 — `.gitignore` patch

- [ ] If `.gitignore` references any of the moved paths, edit them in place:
  - `workspace/` → `.solera/`
  - `workspace/.../{pattern}` → `.solera/.../{pattern}` (preserve the rest of the pattern verbatim)
  - `/progress.md` or `progress.md` (top-level) → `/.solera/progress.md`
  - `/HANDOFF.md` or `HANDOFF.md` (top-level) → `/.solera/HANDOFF.md`
- [ ] If no matches were found in Step 1 → skip; no `.gitignore` change needed.
- [ ] If `.gitignore` did not exist → skip.

### Step 5 — Commit

- [ ] Run `git status` to verify the staged changes match the plan from Step 2.
- [ ] Commit:
  ```
  refactor(solera)!: move workspace/ to .solera/

  - workspace/ -> .solera/ (preserves all subdirs and history via git mv)
  - progress.md -> .solera/progress.md (if present)
  - HANDOFF.md -> .solera/HANDOFF.md (if present)
  - .gitignore patched to match new paths

  BREAKING: Solera v4+ reads from .solera/. Run this skill once per project
  to migrate. Backward compat in Solera v1.x falls back to workspace/
  for one minor version; will be removed in a future Solera minor.

  Solera-Migrate-Step: workspace-to-dotsolera
  ```
- [ ] Final report:
  ```
  Migration complete.

  Moved:
    workspace/         → .solera/
    progress.md        → .solera/progress.md     [if present]
    HANDOFF.md         → .solera/HANDOFF.md      [if present]

  .gitignore: patched | unchanged

  Verify: open the project in your IDE — the file tree no longer shows
  workspace/, progress.md, HANDOFF.md at the root. They live inside
  .solera/ now (hidden from default file-tree views, like .git/ and .vscode/).

  To revert: git revert {commit_hash}
  ```

## Resume Semantics

This skill produces exactly one commit. Resume reduces to "is the commit already there?":

- [ ] Run `git log --grep="Solera-Migrate-Step: workspace-to-dotsolera" -n 1`.
- [ ] If a commit is found → migration already complete. Exit: `"Already migrated (commit {hash}). To revert, run: git revert {hash}"`.
- [ ] If no commit AND `.solera/` exists AND `workspace/` does not → migration was applied but not committed (user did the move manually). Exit with: `"Detected unmanaged migration: .solera/ exists, no migration commit. Stage and commit your changes manually."`
- [ ] Otherwise → proceed from Step 1.

## Human–AI Protocol

This skill has minimal judgment surface — almost everything is mechanical. The single human checkpoint is the BLOCKING confirmation in Step 2.

| AI does | AI does not |
|---------|-------------|
| Use `git mv` to preserve history on every move | Use `mv` or `cp` (loses history) |
| Patch `.gitignore` to match the new paths | Add new `.gitignore` entries the human did not author |
| Exit cleanly on `no` answer at the BLOCKING gate | Roll back partially-applied changes (Step 3 is single-commit; failure means nothing was committed) |
| Skip already-applied work on re-run | Re-apply or duplicate any move |

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| Dirty working tree | `git status --porcelain` non-empty | Refuse; instruct user to commit or stash | Halt |
| Both `.solera/` and `workspace/` exist | Conflict state | Refuse; ask user to inspect manually | Halt |
| `workspace/` missing | Nothing to migrate | Exit with "no workspace/ to migrate" | Halt |
| Already migrated | Migration commit found in `git log` | Exit with already-migrated message | Halt |
| `git mv` fails | E.g. file-permission denied, target already exists | Halt; report exact `git mv` error; advise user to inspect | Halt — no commit |
| User answers `no` at Step 2 | Explicit decline | Exit cleanly without changes | Halt |

## Completion Checklist

- [ ] Working tree clean before start
- [ ] Single BLOCKING confirmation surfaced and approved
- [ ] `git mv workspace .solera` succeeded
- [ ] `progress.md` and `HANDOFF.md` moved if present at root
- [ ] `.gitignore` patched if it referenced any moved path
- [ ] Single commit landed with `Solera-Migrate-Step: workspace-to-dotsolera` trailer
- [ ] Final report shown to user

## Cautions

| Wrong | Correct |
|-------|---------|
| Running with uncommitted work | Commit or stash first |
| Iterating `git mv` per child of `workspace/` | Single `git mv workspace .solera` moves the whole tree atomically |
| Splitting into multiple commits | Single commit only — there is no intermediate-valid state |
| Manually editing `.gitignore` for new entries | Skill only **patches existing** lines; do not introduce new ignore rules |
| Re-running after success "to be sure" | Skill detects the migration commit and exits idempotently — but unnecessary |
