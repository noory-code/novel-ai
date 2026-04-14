# Migrating from Solera v2 to v3

This guide explains how to move an existing v2 project to v3 using `solera-migrate-v2`. The skill itself is the full specification; this doc is the human-facing overview.

## Should you migrate?

v3 is a different shape, not a bigger v2. Consider migrating if you want:

- **A project map that lives** — Concepts on the Living axis instead of Goals/Epics that "complete"
- **Human–AI agreement before scope** — the Milestone Agreement Cycle, where AI must push back before a scope is frozen
- **Immutable Releases** — frozen snapshots of Concept state at release time, so "what was in MVP" stays knowable
- **Story-level branching and PRs** — simpler than v2's Epic-then-Story two-level branch model

Stay on v2.14.0 if you prefer the existing Phase → Goal → Epic → Story hierarchy or if your team has documentation/tooling coupled to v2 paths.

## What changes conceptually

See [work-item-structure.md](./work-item-structure.md) and [architecture.md](./architecture.md) for the full model. The short version:

| v2 | v3 | Why |
|----|----|-----|
| Phase (quarterly) | — (removed) | Time management is off-plugin (calendar, Jira) |
| Goal (service objective) | **Concept** (living) | Goals "completed" — a living map doesn't |
| Epic (deliverable) | **Concept** or a single Story | Most Epics collapse into their parent Concept; small ones become individual Stories |
| Story | **Story** (unchanged in shape) | Gains `contributes_to` + `belongs_to` frontmatter |
| Action Item | **Action Item** (unchanged) | Commit scope tag changes from `[epic-name]` to `[{primary_concept}]` |
| `_epic.md` domain "concept" artifact | **`domain-model`** | Freed the word "Concept" for the living axis |
| Goal-create + Epic-wrap-up promotion hooks | **Story Wrap-up** (single hook) | One promotion point, tied to where evidence is freshest |

Nothing is silently translated. The migration asks the human to **reinterpret** v2 Goals and Epics into v3 Concepts — this is the act you bring to the process.

## What the migration does (at a glance)

`solera-migrate-v2` runs in seven blocking steps:

```
1. Freeze      — git mv all v2 files to _v2-archive/
2. Skeleton    — scaffold v3 dirs + copy identity/catalog
3. Concepts    — AI proposes candidates from v2 Goals/Epics; human approves each
4. Stories     — move completed Stories into stories/ with contributes_to tags
5. pre-v3      — synthetic Milestone framing the v2 era
6. Release     — v2-final immutable snapshot
7. Cleanup     — MIGRATION-NOTES.md + updated progress.md
```

Each step is its own git commit. You can `git reset --hard HEAD~1` to back out of any step and re-run.

## Prerequisites

Before starting:

- [ ] You are on **Solera v3.0.0 or newer** (`cat .claude/plugins/*/plugin.json | grep version`).
- [ ] Your working tree is **clean** (`git status` shows nothing). `solera-migrate-v2` refuses to start otherwise.
- [ ] You have read [quick-start.md](./quick-start.md) so v3 concepts are familiar — the migration asks you to make Concept decisions.
- [ ] If your project has design artifacts outside `workspace/catalog/published/` (e.g., a separate `published/` folder), note the path — you'll pass it as `extra_artifact_dirs`.

## How to run it

Tell Claude:

> Migrate this v2 project to v3.

Claude invokes `solera-migrate-v2` with your project path. If you have an extra artifacts directory:

> Migrate this v2 project to v3. Also fold `published/` into the catalog.

Each step pauses for your approval. Read what the AI proposes, revise as needed, approve to proceed.

## What you will decide

The migration is deliberately opinion-light. You decide:

### Step 2 — Catalog conflicts
If the same filename exists in two source locations (e.g., `workspace/catalog/published/persona/bana.md` AND `published/persona/bana.md`), you pick which wins or keep both with a rename.

### Step 3 — Concept candidates
AI clusters v2 Goals/Epics into Concept proposals and shows its reasoning for each. For every candidate you **approve / rename / merge / split / reject**. Rejected candidates are excluded from migration (recorded in MIGRATION-NOTES.md).

Then for each approved Concept you review a drafted Intent and Current Design — both grounded in specific v2 source sentences. You accept, rewrite, or defer.

### Step 4 — Story ID strategy
v2 Story IDs (`US-001`) are unique per Epic. In v3's flat `stories/`, collisions are expected. Three options:

- **Renumber** — `US-0001`, `US-0002`, … (globally sequential, loses original)
- **Prefix by Epic** (recommended) — `US-auth-001`, `US-onboarding-001`, …
- **Keep and suffix on collision** — `US-001`, `US-001__onboarding`, … (minimal change, inconsistent IDs)

### Step 4 — contributes_to review
AI infers `contributes_to` per Story with a confidence rating. Before the batch runs, you review a random sample of 3–5 Stories. If the sample is right, the batch proceeds; if not, you correct and re-sample. LOW-confidence inferences become `contributes_to: []` and are listed in MIGRATION-NOTES.md for human follow-up.

### Step 6 — Release notes
AI drafts `releases/v2-final/README.md` summarizing what the v2 era contained. You edit freely — this file is immutable after the release is cut, and it's the first durable artifact of your project's history.

### Step 7 — Archive retention
Keep `_v2-archive/` (default) or delete it. Deletion is a normal `git rm` — history remains in git regardless.

## What happens to your v2 data

| Data | After migration |
|------|-----------------|
| **Entire `workspace/` contents** | Archived verbatim to `_v2-archive/workspace-original/` via `git mv` (preserves history). Step 2 rebuilds v3 by copying selectively from the archive. |
| Standard identity files (`mission.md`, `core-values.md`, `vision_*.md`) from any source (workspace or extra dir) | Copied to `workspace/identity/` (v3 location) + kept in archive |
| Non-standard identity files (e.g., `tone-and-manner.md`, `README.md`) | **BLOCKING prompt** at Step 2 — you choose: keep at `workspace/identity/`, route to `catalog/published/_unclassified/identity/`, or skip |
| `identity/journeys/*` | Moved to `catalog/published/journey/` (journeys are journey artifacts, not identity) |
| `workspace/initiative/` | Archived only |
| `workspace/phase/` (all Goals, Epics, Stories) | Archived; **completed Stories** relocated to `workspace/stories/` with updated frontmatter |
| `workspace/catalog/published/` | Merged into `workspace/catalog/published/` (v3 location); `concept/` renamed to `domain-model/` — rename covers both workspace catalog and every extra vault (including nested `published/` subdirs) |
| `extra_artifact_dirs/` contents | Same merge treatment as `catalog/published/`; Step 2.3 handles both top-level and nested `published/` layouts common in Obsidian vaults |
| Catalog types in the v3 mapping (persona, service-map, journey, use-case, domain-model, erd, dto, api-spec, reference) | Moved to their mapped destinations |
| Unknown catalog types (e.g., a custom `schema/` folder) | **BLOCKING prompt** per type — you choose: `_unclassified/{type}/` fallback, or map to an existing v3 type, or skip |
| Loose `.md` files at a vault root (e.g., `app-structure.md`, `README.md` sitting outside any `{type}/` subdir) | **BLOCKING prompt** per file — you choose: route to `catalog/published/_unclassified/misc/`, provide a target path, or skip |
| `workspace/team-process.md` | Copied to v3 location; `workflow_gates` section patched to v3 keys; other sections untouched |
| `progress.md` | Overwritten with v3 three-axis format |
| `HANDOFF.md` | Untouched |
| **git commit history** | **Preserved entirely.** `git mv` used where possible; `git log --follow {path}` works across the v2 → v3 rename |
| v2-era commit messages (`[epic-name][US-NNN][ACT-NNN]`) | **Not rewritten.** They stay as they are in history. Only post-migration commits use the v3 `[{concept}][{story_id}][ACT-NNN]` format |

## What does NOT happen automatically

- **AI does not invent Intent.** Every Concept Intent in the migration is either your own rewrite or a draft composed of traced v2-source sentences. No hallucination allowed.
- **AI does not auto-approve LOW-confidence `contributes_to`.** You review the flagged list.
- **AI does not delete `_v2-archive/`.** You opt in at Step 7.
- **AI does not rewrite v2 commit messages.** History stays truthful.
- **AI does not run a real Milestone Agreement Cycle for pre-v3.** The synthetic milestone skips the cycle because there is no "scope to agree on" — the v2 era's scope is whatever it ended up being.

## After the migration

`MIGRATION-NOTES.md` is generated at the project root. It lists:

- Which v2 sources became which v3 Concepts
- Which sources were excluded and why
- Which Stories need `contributes_to` review
- Any files renamed during catalog merges
- Manual tasks you should work through next (team-process.md, Horizon/Health, first new Milestone, archive deletion)

Your first post-migration task is usually:

> Run `solera-write-milestone` to agree on the scope of the next release.

The `pre-v3` milestone is a historical frame, not a forward plan. Your first real v3 work starts with a new Milestone whose scope Concept depths you agree on with AI before executing any Stories.

## Rolling back

Each of the seven steps is a separate commit. To undo:

```bash
git log --oneline
# find the "freeze v2 workspace" commit — that's the starting point

git reset --hard {commit_before_freeze}
# you're back to pre-migration state
```

If migration is in progress and you want to abandon it partially:

```bash
git reset --hard {last_migration_commit_you_want_to_keep}
# rewinds to that step; the later steps' file changes disappear
```

As long as you haven't pushed or deleted `_v2-archive/`, the migration is fully reversible.

## FAQ

**Q: Can I run the migration on a branch first to test it?**
Yes — create a branch, run `solera-migrate-v2`, review the result, throw the branch away if unsatisfactory.

**Q: What if my project has v2 Stories that were never completed?**
Incomplete Stories (status ⏳ or 🔄 in v2) are skipped by default and listed in MIGRATION-NOTES.md. You can migrate them manually later by moving the files and adding `contributes_to`, or start fresh in v3.

**Q: What about v2 RETROSPECTIVE.md files from Goals/Epics/Phases?**
They stay in `_v2-archive/`. v3 has no Goal/Epic/Phase retrospective concept — business retrospectives happen at Release time via the `README.md` of each release. Your v2 retros remain as historical records in the archive.

**Q: Do I have to use Concepts exactly as AI proposes?**
No. The entire Step 3 exists so you can override AI clustering — merge two candidates, split one into three, reject ones that don't represent a living area. The migration's quality depends on your willingness to push back on AI suggestions.

**Q: What if I decide Concept X was wrong after migrating?**
Run `solera-write-concept` with `mode: deprecate` on the bad Concept; draw a new one; update any Stories that had the wrong `contributes_to`. Standard v3 flow.

**Q: Can I migrate a team project where contributors are on different branches?**
Coordinate carefully. The migration creates massive diffs (every `_story.md` moves, dozens of new files). Do it on trunk when no one else has unmerged branches, or merge all open PRs first. After migration everyone rebases.

## Reference

- [`solera-migrate-v2` SKILL.md](../skills/solera-migrate-v2/SKILL.md) — full skill specification (the authoritative source)
- [MIGRATION-NOTES template](../skills/solera-migrate-v2/assets/migration-notes-template.md) — the structure of the generated notes file
- [work-item-structure.md](./work-item-structure.md) — v3 three-axis model
- [architecture.md](./architecture.md) — skills, Workflow-as-SSOT, gate model
- [quick-start.md](./quick-start.md) — v3 first-project walkthrough
