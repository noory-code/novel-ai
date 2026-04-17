---
name: solera-migrate-v2
user-invocable: true
description: Assisted, non-destructive migration from Solera v2 (Phase/Goal/Epic hierarchy) to v3 (three axes). Every step blocks for human approval; reversible via git until committed.
metadata:
  version: "1.3.0"
  category: meta
  type: unit
  style: procedural
  triggers: [migrate solera, migrate v2 to v3, upgrade solera workspace, v2 to v3]
  uses: []
---

# Migrate Solera v2 → v3 (Assisted)

> 1-shot migration tool. Reads a v2 workspace, freezes it to `_v2-archive/`, and proposes a v3 structure that the human reviews at every step. No automatic decisions about Concept taxonomy — AI suggests, human approves.

## Philosophy

v3 is not a superset of v2. It is a different shape. The axes differ, the hierarchy differs, the commit format differs. A lossless mechanical translation is neither possible nor desirable — v2's Goals/Epics were decomposed by time, v3's Concepts are the living map. **The translation itself is a human act of reinterpretation.** This skill's job is to make that act as assisted and safe as possible, not to automate it.

Rules the skill follows:

- **Non-destructive.** The first action is to move all v2 files to `_v2-archive/`. Nothing in the original locations is ever deleted without the human opting in at Step 7.
- **Blocking on judgment.** Every step where AI makes a proposal (Concept candidates, `contributes_to` inference, Release notes) pauses for human approval before persisting.
- **Git as safety net.** Each major step commits its own changes so the human can `git reset` to any checkpoint.
- **Idempotent re-runs.** If re-invoked on a partially-migrated workspace, the skill detects state (scaffold present, Concepts drafted, Stories moved) and offers to resume rather than restart.

### Why no `## Workflow` section

migrate-v2 is a **one-shot transition skill**, not a work item. It runs once (or resumes once) per project and produces no ongoing lifecycle to drive. Like `solera-release` and `solera-publish-artifacts`, its procedure lives entirely in this SKILL.md — there is no template-level Workflow for `solera-manage-workflow` to read.

## Prerequisites

- A git repository at `{project_path}` with a clean working tree (`git status` shows no uncommitted changes). If dirty, the skill refuses to start.
- A recognizable v2 workspace: any of `workspace/initiative/`, `workspace/phase/`, `workspace/catalog/published/` present.
- The v3 Solera plugin installed (this skill is part of it).

## Input

| Parameter | Required | Description | Example |
|---|---|---|---|
| **project_path** | Y | Project root containing `workspace/` | `/Users/me/banas` |
| **workspace_path** | N | v2 workspace location; default `{project_path}/workspace` | `{project_path}/workspace` |
| **extra_artifact_dirs** | N | Additional artifact roots to fold into the archive/catalog (comma-separated) | `{project_path}/published` |
| **resume_from** | N | Skip earlier steps; accepts the name of a step (`skeleton`, `concepts`, `stories`, `milestone`, `release`, `cleanup`) | `stories` |

## Output

| Step | Output | Path |
|------|--------|------|
| 1. Freeze | Archived v2 data | `{workspace_path}/_v2-archive/` |
| 2. Skeleton | v3 directory structure | `{workspace_path}/concepts/`, `milestones/`, `stories/`, `releases/` + `_index.md` seeds |
| 3. Concepts | Drafted Concept files (human-approved) | `concepts/{id}.md` |
| 4. Stories | Relocated Stories with `contributes_to` tags | `stories/{story_id}-{story_name}/` |
| 5. Milestone (optional) | `pre-v3` milestone summarizing v2 era | `milestones/pre-v3.md` |
| 6. Release | First immutable snapshot | `releases/v2-final/` |
| 7. Cleanup | Updated `progress.md` + migration summary | `progress.md`, `MIGRATION-NOTES.md` |

## Procedure (7 steps, all BLOCKING on approval)

### Step 1 — Freeze

**Policy**: move the **entire** current `{workspace_path}/` contents into an archive, then build v3 fresh in Step 2 by copying selectively from that archive. This avoids ambiguous name-based skipping — `workspace/identity/` may already exist in v2 and still contain v2-only content; deciding to keep or archive it by name alone is wrong. The only safe rule is "archive everything, rebuild from archive."

- [ ] Run `git status --porcelain`. If any output → halt with: "Working tree must be clean. Commit or stash your changes, then re-run."
- [ ] Report what will be frozen:
  - every direct child of `{workspace_path}/` except `_v2-archive/` itself (file or directory, regardless of name) — these all move to `{workspace_path}/_v2-archive/workspace-original/`
  - every `extra_artifact_dirs` entry moves to `{workspace_path}/_v2-archive/extra/{basename}/`
- [ ] **BLOCKING**: show the report and ask `"Freeze these paths to _v2-archive/? (yes/no)"`
- [ ] On approval:
  - Create `{workspace_path}/_v2-archive/workspace-original/`
  - For every direct child of `{workspace_path}/` (except `_v2-archive`): `git mv {workspace_path}/{child} {workspace_path}/_v2-archive/workspace-original/{child}` (preserves git history)
  - For each `extra_artifact_dirs/{path}`: when `{workspace_path}/_v2-archive/extra/{basename}` parent does not exist, `mkdir -p` it; then `git mv {extra_dir} {workspace_path}/_v2-archive/extra/{basename}`
- [ ] After this step, `{workspace_path}/` contains exactly one entry: `_v2-archive/`.
- [ ] Commit with resume trailer:
  ```
  chore(solera): freeze v2 workspace before v3 migration

  Solera-Migrate-Step: 1-freeze
  ```
- [ ] Report: `"Frozen. Entire workspace archived to _v2-archive/workspace-original/. Continuing to Step 2 (skeleton)."`

### Step 2 — Skeleton

After Step 1, `{workspace_path}/` contains only `_v2-archive/`. Step 2 builds the fresh v3 layout from scratch and copies selected content back from the archive.

- [ ] Create v3 directories under `{workspace_path}/`:
  - `identity/` (contents will be filled by Step 2.1)
  - `concepts/` + `_index.md` (from [../solera-write-concept/assets/_index-template.md](../solera-write-concept/assets/_index-template.md))
  - `milestones/` + `_index.md` (from [../solera-write-milestone/assets/_index-template.md](../solera-write-milestone/assets/_index-template.md))
  - `stories/`
  - `releases/` + `_index.md` (from [../solera-release/assets/_index-template.md](../solera-release/assets/_index-template.md))
  - `catalog/published/`

> All source paths below refer to the archive laid out by Step 1:
> `{workspace_path}/_v2-archive/workspace-original/` for the former workspace contents,
> `{workspace_path}/_v2-archive/extra/{name}/` for each former `extra_artifact_dirs` entry.

#### 2.1 Identity copy policy

Identity files may live in multiple locations in v2 Obsidian-style vaults (inside `workspace/identity/` or inside a separate vault root like `{project_path}/published/identity/`). Collect from every plausible source, then classify:

- [ ] Collect identity-source candidates in priority order:
  1. `_v2-archive/workspace-original/identity/*.md` (from the former workspace identity directory)
  2. `_v2-archive/extra/*/identity/*.md` (from each archived extra vault)
- [ ] For each candidate file, classify:
  - **v3 standard identity** (`mission.md`, `core-values.md`, `vision_*.md`) → stage to copy into `{workspace_path}/identity/`.
  - **Journeys subdir** (`.../identity/journeys/*`) → stage to move into `catalog/published/journey/` — these are journey artifacts that happened to live under identity in v2.
  - **Non-standard identity files** (`tone-and-manner.md`, `README.md`, and any other `.md` under an identity dir that is not standard): gather into a list for the BLOCKING prompt below.
- [ ] **BLOCKING** (only if non-standard files found): for each non-standard file, ask `"Found '{filename}' under identity. Choose: (1) keep at workspace/identity/{filename}  (2) move to catalog/published/_unclassified/identity/{filename}  (3) skip"`. Record decisions in the step log.
- [ ] Apply all decisions: copy standard files to `workspace/identity/`, move journeys to `catalog/published/journey/`, handle non-standard per human choice. Leave archive copies intact (the archive is the full record).
- [ ] If **no** standard identity files were found in any source → warn the human: `"No standard identity files found. You may need to run solera-write-identity manually after migration. Continue?"` — require confirmation.

#### 2.2 team-process.md

- [ ] If `_v2-archive/workspace-original/team-process.md` exists → copy to `{workspace_path}/team-process.md` and **patch only the `workflow_gates` section** to v3 keys (remove `epic.use_case`, `epic.concept`; add `milestone.agree`, `concept.align`). Other sections preserved as-is.
- [ ] If no team-process.md was found in the archive → log a reminder in the eventual MIGRATION-NOTES.md Manual Tasks: run `solera-init` post-migration to populate it via the Kickoff Interview.

#### 2.3 Catalog merge

Merge archived catalogs from both the original workspace and every extra vault into the fresh `{workspace_path}/catalog/published/`. Handle v2's `concept/` rename, unknown types, and loose files.

- [ ] **Rename v2 `concept/` → v3 `domain-model/` everywhere it appears**. Any of the following source paths should route to `catalog/published/domain-model/`:
  - `_v2-archive/workspace-original/catalog/published/concept/`
  - `_v2-archive/extra/*/concept/`
  - `_v2-archive/extra/*/published/concept/` (nested vault layouts)
- [ ] Enumerate every `{type}/` subdir from all relevant source locations:
  - `_v2-archive/workspace-original/catalog/published/{type}/`
  - `_v2-archive/extra/*/{type}/` (top level of each extra vault)
  - `_v2-archive/extra/*/published/{type}/` (nested `published/` inside extra vaults — common Obsidian layout)
- [ ] For each `{type}` found, classify using the `solera-publish-artifacts` Move Mapping table:
  - **Known type** (persona, service-map, journey, use-case, domain-model, erd, dto, api-spec, reference) → destination per that table.
  - **Unknown type** (e.g., `schema/`, any custom folder): **BLOCKING** one-shot prompt per type: `"Found unknown catalog type '{type}' (from {source}). Choose: (1) move to catalog/published/_unclassified/{type}/  (2) map to an existing v3 type (provide target)  (3) skip (leave only in _v2-archive)"`. Apply the decision.
- [ ] **Loose files at vault roots**: scan for `.md` files that sit **directly** at the root of any extra vault (e.g., `_v2-archive/extra/{name}/README.md`, `_v2-archive/extra/{name}/app-structure.md`) rather than inside a `{type}/` subdir. Also scan `_v2-archive/workspace-original/` for loose `.md` files that aren't `team-process.md`.
  - **BLOCKING** one-shot prompt per loose file: `"Found loose file '{path}'. Choose: (1) copy to catalog/published/_unclassified/misc/{filename}  (2) provide a target path  (3) skip"`. Apply the decision.
- [ ] **Filename collision detection during merge**: if the same filename from different sources targets the same destination:
  - **BLOCKING**: show a short diff summary and ask `"Which version wins? (1) source A  (2) source B  (3) both (rename the later one to {name}__{source_tag}.md)"`.

- [ ] Commit with resume trailer:
  ```
  chore(solera): scaffold v3 workspace skeleton

  Solera-Migrate-Step: 2-skeleton
  ```
- [ ] Report: `"Skeleton created. Identity copied (X standard, Y non-standard per choice). Catalog merged (Z known types, W unknown routed to _unclassified/ or mapped, L loose files handled). Continuing to Step 3 (concepts)."`

### Step 3 — Concept candidate proposal

This is the most judgment-heavy step. AI scans v2 artifacts and proposes Concepts; human approves, merges, splits, or rejects each.

- [ ] **Scan phase**: read every `_goal.md`, `_epic.md`, `_v2-archive/workspace-original/initiative/*/roadmap.md`, `_v2-archive/workspace-original/initiative/*/README.md`, `_v2-archive/workspace-original/phase/*/README.md` in the archive. Also read any `catalog/published/persona/*.md`, `service-map/*.md`, `journey/*.md`, `use-case/*.md`, `domain-model/*.md` (the v3 locations, already populated by Step 2) for cross-references.
- [ ] **Cluster phase**: group Goals/Epics by thematic area. Heuristics (apply in order; AI should surface its reasoning):
  - Same `feature/*` tag in frontmatter → same Concept candidate.
  - Same Goal → split only if multiple Epics clearly describe distinct long-lived areas (e.g., G1-auth-onboarding → Authentication + Onboarding).
  - Cross-Goal Epics with the same theme → merge into one Concept even if they lived under different Goals.
  - Persona/service-map linkage as tiebreaker: if two Epic candidates reference the same persona, prefer merging.
- [ ] **Draft proposal**: for each candidate, produce:

  ```
  Candidate {N}: {PROPOSED_CONCEPT_NAME}
    Source (v2):
      - Goal: G1-auth-onboarding
      - Epics: 01-user-auth, 02-admin-redesign(auth portion)
    Personas referenced: bana, hero
    Service maps referenced: admin
    Proposed Intent (draft — YOU must rewrite in Step 3b):
      "사용자가 자신의 정체를 증명하고 적절한 권한을 받는 방법."
    Confidence: high | medium | low
    Notes:
      - 01-user-auth is complete; 02-admin-redesign is marked in-progress.
      - Apple OAuth mentioned in _epic.md but deferred.
  ```

- [ ] **BLOCKING**: present the full list of candidates. Ask the human to, for each candidate:
  - **Approve as-is** (AI will draft concept file; human rewrites Intent before save).
  - **Rename** the concept_id and re-propose.
  - **Merge** with another candidate.
  - **Split** into multiple Concepts (AI re-clusters the sources).
  - **Reject** (none of these sources become a Concept; recorded as "excluded from migration — rationale: …").

- [ ] **Step 3b — batch Concept authoring**: for each approved candidate, present a draft block:

  ```
  Concept {n}/{N}: {concept_id}

  Draft Intent (from v2 sources):
    "사용자가 자신의 정체를 증명하고 적절한 권한을 받는 방법."
  Source sentences:
    - "사용자 인증" (G1-auth-onboarding/_goal.md line 16)
    - "역할 시스템" (G0-infrastructure/epics/04-build-roles/_epic.md)

  Draft Current Design:
    ...

  Draft Related Artifacts:
    - Personas: [[persona/bana]], [[persona/hero]]
    - Service Map: [[service-map/admin]]
  ```

  Per-candidate options (do not fall back to individual `solera-write-concept` invocations — that would require re-entering Intent for each):

  - **Accept draft** → write the file as-proposed. (Human can still edit Intent freely afterward.)
  - **Rewrite Intent** → human provides a new Intent inline; AI regenerates the Current Design draft preserving any human edits.
  - **Defer** → skip writing this Concept for now; listed in MIGRATION-NOTES.md under "deferred Concepts" for later `solera-write-concept create` invocation.

  Batch-processing constraint: the skill writes each accepted Concept file directly (matching the v3 template) rather than invoking `solera-write-concept` per candidate. This honors the "AI must not invent Intent" rule by **grounding every sentence in an explicit v2 source**, not by relying on the interactive-Intent BLOCKING gate.

- [ ] After all approved/rewritten Concepts are written: update `concepts/_index.md`.
- [ ] Commit with resume trailer:
  ```
  chore(solera): migrate concepts from v2 (N concepts drafted)

  Solera-Migrate-Step: 3-concepts
  ```

### Step 4 — Story relocation with `contributes_to` inference

- [ ] **Discover Stories** in the archive: every directory under `_v2-archive/workspace-original/phase/*/goals/*/epics/*/` whose name matches `US-NNN-*` or `TS-NNN-*` and which contains `_story.md`.
- [ ] **Propose a global ID strategy**. v2 Story IDs (`US-001`, `TS-001`) are unique only within an Epic, so collisions are expected in v3's flat `stories/`. AI proposes one of:
  - **Renumber**: assign new global IDs (`US-0001`, `US-0002`, …) in discovery order. Loses the original ID — captured in the origin comment.
  - **Prefix by Epic**: `US-auth-001` instead of `US-001`. Preserves original number at the cost of slightly noisier IDs.
  - **Keep and suffix on collision**: keep `US-001` for the first, use `US-001__{epic}` for later conflicts. Minimally invasive but inconsistent.
- [ ] **BLOCKING**: ask the human which strategy to use. Default recommendation: **Prefix by Epic** (reads well in `git log`).
- [ ] **Infer `contributes_to` for each Story**. Heuristics:
  - Read the Epic's `_epic.md` frontmatter tags (`feature/auth` → `authentication` Concept if that was approved in Step 3).
  - Cross-check `_story.md` body for explicit Concept-relevant language.
  - If the Story is `TS-*` (technical), often maps to the same Concept as its sibling `US-*` Stories in the same Epic.
  - If no clear match: tag as `contributes_to: []` (empty) and flag for human review.
- [ ] Assemble a **batch report**:
  ```
  Story relocation plan (42 stories discovered):

  1. US-auth-001 (was 01-user-auth/US-001-login-screen)
     contributes_to: [authentication]    (confidence: high)
     belongs_to: pre-v3
     completed: yes (v2 status: completed)

  2. US-auth-002 (was 01-user-auth/US-002-login-flow-mvi)
     contributes_to: [authentication]    (confidence: high)
     belongs_to: pre-v3

  3. TS-clean-001 (was 04-clean-architecture/TS-001-ui-flow-cache-package)
     contributes_to: []                  (confidence: LOW — no single-feature match)
     belongs_to: pre-v3
     ⚠️ needs human review

  ...
  ```
- [ ] **BLOCKING sample review**: ask the human to review 3–5 random samples from the plan. If approved, process all; if corrections needed, accept per-entry overrides.
- [ ] **Execute the batch**:
  - For each Story: `git mv {archive_story_path} {workspace_path}/stories/{new_id}-{name}/` (preserves git history).
  - Patch `_story.md`:
    - Add/replace frontmatter fields: `story_id: {new_id}`, `story_name: {name}`, `contributes_to: [...]`, `belongs_to: pre-v3` (default — may be changed later).
    - Replace old `status: completed` → `status: ✅ Complete`.
    - Prepend origin comment:
      ```
      <!-- v2 origin: _v2-archive/workspace-original/phase/{phase}/goals/{goal}/epics/{epic}/{old_id}-{name}/ -->
      ```
  - Patch each `ACT-NNN-*.md` in the Story: prepend the same origin comment.
  - **Do not** rewrite existing git commit messages from v2 (`[epic-name][US-NNN][ACT-NNN]`). The git log preserves v2-era commits as-is; only the filesystem layout and frontmatter change.
- [ ] Report progress: `"Relocated X/Y Stories. Z flagged for human review (empty contributes_to)."`
- [ ] Commit with resume trailer:
  ```
  chore(solera): migrate N stories to v3 stories/

  Solera-Migrate-Step: 4-stories
  ```

### Step 5 — `pre-v3` synthetic Milestone (required)

`solera-release` requires a released milestone. Migration always creates one synthetic milestone (`pre-v3`) that captures the v2 era as a single scope-agreed block, so Step 6 can operate.

- [ ] Write `{workspace_path}/milestones/pre-v3.md` directly (not via `solera-write-milestone`, which would trigger an interactive Agreement Cycle — inappropriate for a synthetic historical milestone):
  - Frontmatter: `id: pre-v3`, `name: "Pre-v3 era"`, `status: released`, `target_date` omitted, `created: today`, `released_at: today`
  - `# Scope`: one line per migrated Concept with the depth note `"as of v3 migration"`
  - `# AI Analysis`: `"Synthetic milestone. No agreement cycle ran; scope is the full set of migrated Concepts at migration time. Analysis rounds do not apply to retrospective synthesis."`
  - `# Agreement Log`: single entry dated today: `"Milestone created by solera-migrate-v2 to frame the v2 era for release snapshot."`
  - `# Exit Criteria`: one entry per Concept: `"Current Shape reflects whatever the v2 era had produced."` (All treated as met by construction.)
  - `# Accepted Risks`: the list of Stories flagged with empty `contributes_to` from Step 4.
- [ ] Update `milestones/_index.md` — add `pre-v3` under `## Released`.
- [ ] Commit with resume trailer:
  ```
  chore(solera): create pre-v3 synthetic milestone

  Solera-Migrate-Step: 5-milestone
  ```

### Step 6 — `releases/v2-final/` snapshot

- [ ] Invoke `solera-release` with `milestone_id: pre-v3`, `release_tag: v2-final`. (The `pre-v3` milestone is always present — see Step 5.)
- [ ] AI drafts `README.md` for the release, summarizing:
  - Count of Phases, Goals, Epics, Stories in the v2 archive
  - Top 3 completed Stories (by date or recency)
  - Which Concepts emerged from Step 3 and what era they represent
  - Accepted risks: "IDs renamed / contributes_to inferred by AI for some Stories — see `MIGRATION-NOTES.md`"
- [ ] **BLOCKING**: human reviews and edits the README draft; approves before the release is finalized.
- [ ] `solera-release` writes `releases/v2-final/` (immutable snapshot, ❄️ markers on concept copies, `.released` marker).
- [ ] Commit with resume trailer:
  ```
  chore(solera): freeze v2 era as release v2-final

  Solera-Migrate-Step: 6-release
  ```

### Step 7 — Cleanup + migration notes

- [ ] Generate `{project_path}/MIGRATION-NOTES.md` using [assets/migration-notes-template.md](assets/migration-notes-template.md). Include:
  - Date of migration
  - Counts: {N concepts}, {M stories moved}, {K stories needing review}, {J artifacts in catalog}
  - ID strategy chosen in Step 4
  - List of excluded v2 Goals/Epics from Step 3 with rationale
  - Known manual tasks ("these Stories still have empty contributes_to")
- [ ] Rewrite `{project_path}/progress.md` to v3 format (reference `{workspace_path}/_v2-archive/workspace-original/progress.md` if present, otherwise start from scratch).
- [ ] **BLOCKING**: ask `"Delete _v2-archive/? (default: keep. It's safe to keep — git history stores everything.)"`
  - Default: **keep**. The archive is not heavy.
  - If the human chooses delete: `git rm -r _v2-archive/`.
- [ ] Commit with resume trailer:
  ```
  chore(solera): complete v2→v3 migration (see MIGRATION-NOTES.md)

  Solera-Migrate-Step: 7-cleanup
  ```
- [ ] Final report:
  ```
  Migration complete.

  Concepts created: {N}  (see concepts/_index.md)
  Stories migrated: {M}  ({K} need contributes_to review — see MIGRATION-NOTES.md)
  Release cut:     v2-final
  _v2-archive:     kept | deleted

  Next step: run `solera-write-milestone` to agree on your first post-v3 scope.
  ```

## Resume Semantics

If re-invoked on a workspace with partial v3 state, the skill determines the last completed step **deterministically** from commit trailers, then falls back to filesystem signals only if the trailers are absent (e.g., amended commits, repo rebased).

**Primary signal — `Solera-Migrate-Step` trailer in recent commits**:

- [ ] Run `git log --grep="Solera-Migrate-Step:" --format="%H %s%n%b" -n 20` on the current branch.
- [ ] The highest-numbered step found (`7-cleanup` > `6-release` > … > `1-freeze`) = last completed step.
- [ ] Next step = that number + 1. If `7-cleanup` is present, the migration is already complete → halt with `"Migration already complete (commit {hash}). To revise, edit files directly or cut a new release."`.

**Fallback signal — filesystem state** (only when no trailer is found):

| Signal | Step inferred complete |
|---|---|
| `_v2-archive/` exists, `workspace/catalog/published/` populated (possibly with `_unclassified/`) | Step 1, 2 |
| `concepts/_index.md` has entries | Step 1, 2, 3 |
| `stories/` has Stories with `contributes_to` | Step 4 |
| `milestones/pre-v3.md` exists | Step 5 |
| `releases/v2-final/.released` exists | Step 6 |
| `MIGRATION-NOTES.md` exists | Step 7 |

If the trailer-derived step and filesystem-derived step disagree (e.g., trailer says Step 3 done but `stories/` already has tagged Stories), trust the filesystem and warn: `"Commit trailer says step {N}, but filesystem suggests step {M}. Resuming from step {max(N,M)+1}."`

In all cases the skill asks `"Resume from Step {N+1}? (or restart from earlier step)"` before proceeding.

## Human–AI Protocol

This skill is a **transition skill** — a bridge from one project model to another. The human is the final arbiter of how v2 knowledge translates to v3, and AI should be especially humble here.

| AI does | AI does not |
|---------|-------------|
| Cluster v2 Goals/Epics into Concept candidates with source traceability | Collapse or merge Concepts without human confirmation |
| Infer `contributes_to` with confidence ratings | Mark LOW-confidence inferences as acceptable without human review |
| Preserve v2 git history via `git mv` | Rewrite historical commits or remove `_v2-archive/` without explicit consent |
| Offer ID strategies and let the human pick | Silently renumber Story IDs |
| Flag empty `contributes_to` Stories for later review | Drop them or force a guess |

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| Dirty working tree | `git status --porcelain` non-empty | Refuse to start; instruct user to commit or stash | Halt |
| Not a v2 workspace | No `phase/`, `initiative/`, or `catalog/published/` | Halt; advise `solera-init` for fresh v3 | Halt |
| Already migrated | `concepts/` has files and no `_v2-archive/` | Halt; "no v2 data to migrate" | Halt |
| Partial state with ambiguity | Detection heuristics conflict | Present state report; ask user which step to resume | Pause |
| Invoked sub-skill fails | `solera-write-concept` / `solera-release` error | Report; do not commit; allow retry | Pause |
| Conflict during catalog merge | Same filename from two sources | BLOCKING 3-option prompt | Pause |
| ID strategy rejected by human | All three options declined | Ask for a custom strategy; accept free-form | Pause |

## Completion Checklist

- [ ] Working tree clean at start; git history preserved via `git mv`
- [ ] `_v2-archive/` contains all v2 files; none deleted without explicit consent
- [ ] v3 skeleton present (concepts/, milestones/, stories/, releases/, catalog/published/)
- [ ] Identity and team-process.md copied (with gate keys patched)
- [ ] All approved Concepts drafted via `solera-write-concept` (each Intent human-written)
- [ ] All discovered Stories relocated with `contributes_to`; flagged ones listed in MIGRATION-NOTES.md
- [ ] `pre-v3` milestone (if chosen) + `v2-final` release cut
- [ ] `MIGRATION-NOTES.md` written at project root
- [ ] `progress.md` rewritten in v3 format
- [ ] Each major step is its own commit (7 commits max — reversible)

## Cautions

| Wrong | Correct |
|-------|---------|
| Running on a dirty working tree | Commit or stash first; skill refuses otherwise |
| Using `rm -rf _v2-archive/` mid-migration | Keep until Step 7; deletion is optional |
| Accepting AI's Concept clusters blindly | Every candidate is human-approvable — split / merge / reject as needed |
| Auto-approving `contributes_to` inferences | Review the 3–5 sample and fix any misclassified before batch runs |
| Rewriting v2 commit messages to the new format | Leave v2 commit history alone. The new format applies to post-migration commits only |
| Re-invoking the skill to "fix" an already-completed migration | Edit the files directly or cut a new Release with corrections — re-running is for resuming, not repairing |
