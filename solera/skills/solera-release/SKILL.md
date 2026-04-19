---
name: solera-release
user-invocable: true
description: Freeze an achieved Milestone into an immutable release snapshot — the Moment 4 skill that closes 결과 확정.
metadata:
  version: "1.0.1"
  category: writing
  type: unit
  style: procedural
  triggers: [release, freeze milestone, create release, cut release, snapshot release, release tag]
  uses: []
---

<!-- SSOT: ../../docs/reference/axes-and-status.md — Release immutability (`.released` marker) and `in_scope` relation live there -->

# Release

> A Release is the **immutable snapshot** of a project at one moment.
> When a Milestone's Exit Criteria are met, this skill freezes the Concepts of that moment so future work cannot quietly rewrite the past.
> This is Solera's Moment 4 (결과 확정).

## Philosophy

Concepts live on the Living Axis — they keep changing. Without a freeze mechanism, "Authentication at MVP time" becomes irrecoverable as soon as someone edits `concepts/authentication.md`. Releases are Solera's guarantee that **the past stays the past**.

A Release snapshot contains:

- **A copy of every in-scope Concept file** at release time — under `releases/{tag}/concepts-snapshot/`.
- **A manifest of contributing Stories** — `stories-manifest.md` lists every Story whose `contributes_to` hit one of the scope Concepts and completed before release.
- **A release note** — `README.md` summarizing what this Release represents, written by AI and approved by the human.

Once written, the `releases/{tag}/` directory must be treated as read-only by convention. This skill never modifies an existing release.

### Why no `## Workflow` section inside a Release

Unlike Concept / Milestone / Story files, a Release is **not a work item**. It has no lifecycle of its own — it is the immutable output produced at a single moment and then never executed again. The procedure that produces it lives here, in this SKILL.md. There is nothing for `solera-manage-workflow` to drive inside `releases/{tag}/`, which is why no Workflow section appears in any snapshot file.

## Prerequisites

- `{project_path}/.solera/milestones/{milestone_id}.md` exists with `status: released` (set via `solera-write-milestone --mode=mark-released`).
- `{project_path}/.solera/concepts/` contains every Concept listed in the milestone's `# Scope`.
- `{project_path}/.solera/releases/` directory (created by `solera-init` or on first invocation).

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas |
| **milestone_id** | Y | The milestone to freeze | mvp |
| **release_tag** | Y | Kebab-case tag, unique | v0.1-mvp |
| **create_git_tag** | N | Also run `git tag {release_tag}` (default: false) | true |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create | Release directory | `{project_path}/.solera/releases/{release_tag}/` | Final (immutable) |
| Create | Release README | `releases/{release_tag}/README.md` | Final (immutable) |
| Create | Concepts snapshot | `releases/{release_tag}/concepts-snapshot/*.md` | Final (immutable) |
| Create | Stories manifest | `releases/{release_tag}/stories-manifest.md` | Final (immutable) |
| Wrap-up | Release index entry | `releases/_index.md` | Mutable (index only) |
| Wrap-up (opt.) | Git tag | repo `.git/refs/tags/{release_tag}` | Final |

## Procedure

### 1. Setup

- [ ] Confirm `{project_path}/.solera/milestones/{milestone_id}.md` exists and has `status: released`.
  - If status is `agreed` or `in-progress`: stop and advise `solera-write-milestone --mode=mark-released` first.
  - If file is missing: stop.
- [ ] Read the milestone's `# Scope` section; extract the list of Concept IDs.
- [ ] For each Concept ID: confirm `concepts/{id}.md` exists.
  - Any missing → stop and list them.
- [ ] Ensure `releases/` and `releases/_index.md` exist (scaffold `_index.md` from [assets/_index-template.md](assets/_index-template.md) if missing).
- [ ] Check `releases/{release_tag}/` does **not** exist.
  - Exists → stop and refuse (releases are immutable — the human must choose a new tag or delete the existing one manually).

### 2. Gather contributing Stories

- [ ] Scan `stories/*/\_story.md` for Stories where:
  - `contributes_to` intersects the Milestone's scope Concepts, AND
  - The Story's status is ✅ complete (read from the status field or `_story.md` header).
- [ ] Record for each: `{story_id}`, `{story_name}`, `contributes_to`, `belongs_to`, commit range (first and last ACT commit hashes if available via git log on the Story folder path).
- [ ] If a Story has `belongs_to: {milestone_id}` but is **not yet complete**: warn the human.
  > "Story {id} belongs to this milestone but is not complete. Including a release now will leave it outside the snapshot. Continue?"
  - Require explicit human confirmation to proceed.

### 3. Snapshot Concepts

- [ ] Create `releases/{release_tag}/concepts-snapshot/`.
- [ ] For each in-scope Concept ID:
  - Copy `concepts/{id}.md` → `releases/{release_tag}/concepts-snapshot/{id}.md`.
  - Prepend to the copy (immediately after frontmatter):
    ```
    > ❄️ Snapshotted for release `{release_tag}` on {YYYY-MM-DD}. Immutable.
    ```
  - Do **not** modify the original `concepts/{id}.md`.
- [ ] Also copy `concepts/_index.md` → `releases/{release_tag}/concepts-snapshot/_index.md` (for context; same immutable marker).

### 4. Write Stories manifest

- [ ] Write `releases/{release_tag}/stories-manifest.md` using [assets/stories-manifest-template.md](assets/stories-manifest-template.md).
- [ ] For each Story from Step 2, produce one row. Sort by Story ID ascending.
- [ ] If git is available, include commit hash range per Story. If not, leave blank.

### 5. Write Release README (AI draft → human approval)

- [ ] Generate draft using [assets/release-notes-template.md](assets/release-notes-template.md). Fill:
  - **Overview** — 2–3 sentence AI summary of what this Release represents. Base it on: milestone `# Scope`, Concepts' Current Shape at snapshot time, Stories completed.
  - **Included Concepts** — name + one-line Intent of each in-scope Concept.
  - **Story Count** — total completed Stories contributing.
  - **Accepted Risks** — copied from milestone `# Accepted Risks` if present.
  - **Follow-up Candidates** — AI suggestion of what is *not* in this Release but was discussed (e.g., items removed from scope in Agreement Log).
- [ ] Present the draft to the human:
  > "Release note draft. Review and edit — this is the immutable record of {release_tag}."
- [ ] **BLOCKING**: require explicit human confirmation. Allow edits or full rewrite. The human has the final word on wording.
- [ ] Save approved README to `releases/{release_tag}/README.md`.

### 6. Immutability lock (convention-level)

- [ ] Verify all 3 required files present: `README.md`, `concepts-snapshot/`, `stories-manifest.md`.
- [ ] Write `releases/{release_tag}/.released` marker file containing:
  ```
  release_tag: {release_tag}
  milestone_id: {milestone_id}
  released_at: {YYYY-MM-DD HH:MM}
  by: solera-release v{skill_version}
  ```
- [ ] This marker is how other skills detect "do not touch" (no filesystem permission change — pure convention).

### 7. Optional git tag

- [ ] If `create_git_tag == true`:
  - Confirm we are in a git repo (`git rev-parse --git-dir`).
  - Confirm no uncommitted changes that would make the tag ambiguous; if dirty, ask the human to confirm.
  - Run `git tag -a {release_tag} -m "Solera release: {milestone_id}"`.
  - Do **not** push (user pushes manually).

### 8. Wrap-up

- [ ] Update `releases/_index.md`:
  - Prepend the new entry under `## Released` (most recent first).
  - Format: `- [{release_tag}](./{release_tag}/README.md) — {milestone_id}, {released_at}`.
- [ ] Emit summary to user:
  > "Release `{release_tag}` frozen. {N} Concepts snapshotted, {M} Stories included. README approved. {Git tag created | No git tag}."

## Human–AI Protocol

This skill is a **Moment 4 skill** (Milestone Reached → freeze). The collaboration rule is:

| AI does | AI does not |
|---------|-------------|
| Draft the Overview and Follow-up sections of the README | Finalize README without human approval |
| Detect incomplete Stories that would fall outside the snapshot | Silently exclude them |
| Copy Concept files verbatim into the snapshot | Edit any file inside `releases/{tag}/` after it is written |
| Refuse to overwrite an existing `releases/{tag}/` | Delete or rewrite an existing release |

Releases are Solera's **only truly immutable artifact**. The AI's job is to make that immutability trustworthy.

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| Milestone not released | `status != released` | Advise `solera-write-milestone --mode=mark-released` | Skill halts |
| Missing Concept | Scope references missing file | List missing; halt | Skill halts |
| Tag collision | `releases/{tag}/` exists | Refuse; require new tag or manual cleanup | Skill halts |
| Incomplete Story in scope | `belongs_to: {this}` + not ✅ | Warn, require human confirm to proceed | Skill pauses |
| Git tag creation failed | git error | Report error; release files already written | Skill halts but snapshot is intact |
| README not approved | Human rejects draft | Loop on draft+edit until approved | Skill pauses |

## Completion Checklist

- [ ] `releases/{release_tag}/README.md` present and human-approved
- [ ] `releases/{release_tag}/concepts-snapshot/` contains one `.md` per in-scope Concept + `_index.md`
- [ ] Every snapshot file has the ❄️ immutability marker
- [ ] `releases/{release_tag}/stories-manifest.md` present
- [ ] `releases/{release_tag}/.released` marker file written
- [ ] `releases/_index.md` updated
- [ ] (If requested) git tag created locally
- [ ] Original `concepts/*.md` files untouched

## Examples

### Example: release v0.1-mvp for banas

Invocation:
```
Skill(name="solera-release", args={
  "project_path": "banas",
  "milestone_id": "mvp",
  "release_tag": "v0.1-mvp",
  "create_git_tag": true
})
```

After success, tree:
```
banas/.solera/releases/
├── _index.md                         # updated
└── v0.1-mvp/
    ├── .released
    ├── README.md                     # AI-drafted, human-approved
    ├── concepts-snapshot/
    │   ├── _index.md
    │   ├── authentication.md         # with ❄️ marker
    │   ├── onboarding.md
    │   └── liquor-search.md
    └── stories-manifest.md
```

Original `concepts/*.md` are unchanged. `git tag v0.1-mvp` exists locally.
