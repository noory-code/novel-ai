---
name: solera-migrate-v4-to-v5
user-invocable: true
description: Migrate a Solera v4.x workspace to v5.0 — promote top-level Personas to Roles, relabel `Journey.walks` and `Narrative.about` to their new Role-based semantics, and seed `.solera/roles/` with the promoted Roles.
metadata:
  version: "1.0.0"
  category: migration
  type: unit
  style: procedural
  triggers: [migrate v4 to v5, solera v4 to v5, upgrade solera to v5, promote personas to roles]
  uses: []
---

<!-- SSOT: ../../docs/reference/axes-and-status.md — v5 schema of Role /
     Persona / Journey / Narrative is canonicalised there. -->

# Migrate Solera v4 → v5 (Role introduction)

> A single-commit, BLOCKING-confirmation, idempotent migration that promotes
> v4 top-level Personas into the new Role entity, labels Journeys and
> Narratives for the v5 Role-based schema, and leaves the workspace ready
> for the Actors canvas.

## Philosophy

v4 used `Persona` for both **structural user classes** ("admin", "fan") and **individual archetypes** ("성덕 30대 Alice"). v5 splits these two into separate entities — `Role` (structural) and `Persona` (archetype under a Role). Most v4 workspaces used Personas exclusively for the structural sense, so the default migration promotes every top-level Persona to a Role; the human can opt-in on a file-by-file basis to keep a particular Persona as an archetype under its chosen Role.

This skill is **idempotent**: a second run on an already-migrated workspace detects the presence of `.solera/roles/` and offers to replay only the parts the human flagged as incomplete.

## Prerequisites

- `{project_path}` has a `.solera/` directory that matches the v4 layout (at least one of `personas/`, `journeys/`, `narratives/` present).
- Working tree is clean (no uncommitted changes). **HALT** with a diff pointer if not.
- v5 plugin installed (this skill's presence is evidence).

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project root containing `.solera/` | `.` |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Roles | Promoted Role files | `.solera/roles/*.md` | Final |
| Personas | Re-stamped Persona files (with `role:` field) | `.solera/personas/*.md` | Final |
| Journeys | Re-stamped Journey files (walks=Role id; optional walked_by) | `.solera/journeys/*.md` | Final |
| Narratives | Re-stamped Narrative files (`about_roles:` / `about_personas:`) | `.solera/narratives/*.md` | Final |
| Log | Migration report | `.solera/MIGRATION-v4-to-v5.md` | Final |

## Procedure

### 1. Pre-flight (BLOCKING)

- [ ] **Working tree clean**: run `git status --porcelain` (or equivalent). If any modified files exist, halt and advise the user to commit or stash first.
- [ ] **Backup hint**: suggest the user tag the pre-migration state (`git tag pre-solera-v5`) before proceeding. Proceed only after explicit confirmation.
- [ ] **Mode detect**:
  - Pure v4 workspace: `.solera/personas/` exists; `.solera/roles/` does NOT exist → full migration.
  - Partial v5 workspace: `.solera/roles/` exists but some `personas/*.md` still lack `role:` → offer a **repair-only** pass (skip Step 2 / Step 3's already-migrated files).
  - Already v5: every Persona has `role:`, every Narrative has `about_roles:`, directory layout complete → report "already migrated" and exit.

### 2. Promote Personas to Roles (per-file AskUserQuestion)

For each `.solera/personas/*.md` (skip `_index.md`):

- [ ] Read the file. Extract `id`, `name`, frontmatter `status`, `parent` (if any), and the `# Identity` section body as the description candidate.
- [ ] Ask the human with `AskUserQuestion`:
  - `question`: `"Is `{id}` a structural user class (Role) or an individual archetype (Persona)?"`
  - `options`:
    - `Role — promote to .solera/roles/{id}.md` (**default**). Preserves every scalar field; `# Identity` becomes the Role's `# Description`; `# Goals`/`# Pains`/`# Triggers`/`# Quotes`/`# Channels` are appended as an HTML-commented `<!-- v4 archive -->` block so nothing is lost.
    - `Persona — keep in place, assign a Role`. Follow-up question: which Role should this Persona belong to? (list the Roles we've promoted so far + literal `Create a new parent Role now`).
    - `Split — promote Role AND leave a Persona archetype`. Writes `.solera/roles/{id}.md` with a distilled description + `.solera/personas/{id}-archetype.md` preserving the detailed fields, with `role: {id}`.
- [ ] Apply the chosen action. Record the decision in memory so the log/idempotency pass can see it.

### 3. Re-stamp Journeys (walks → Role id)

For each `.solera/journeys/*.md` (skip `_index.md`):

- [ ] Read the file, inspect its current `walks` value.
- [ ] Look up how `walks` was resolved in Step 2:
  - If the Persona was promoted to Role: the value stays the same (same id, now interpreted as a Role). Add an editorial comment to the log.
  - If the Persona was kept as a Persona: re-write `walks` to that Persona's `role` (from Step 2 follow-up), and append `walked_by: [{original_walks_id}]` so the concrete archetype is preserved.
  - If the referent doesn't exist at all (orphan): leave `walks` as-is; parser will flag `broken_walks_ref`.

### 4. Re-stamp Narratives (about → about_roles / about_personas)

For each `.solera/narratives/*.md` (skip `_index.md`):

- [ ] Read frontmatter. If `about:` is still present:
  - Partition the list by the Step 2 decisions: ids promoted to Role go to `about_roles`; ids kept as Persona go to `about_personas`.
  - If every id was kept as Persona (no Role remains): add that Persona's Role to `about_roles` (1+ is required) and the Persona id to `about_personas`.
  - Delete the old `about:` key.

### 5. Seed missing structure

- [ ] Create `.solera/roles/_index.md` from [../solera-write-role/assets/_index-template.md](../solera-write-role/assets/_index-template.md) if absent.
- [ ] Append "Active Roles" row to `.solera/progress.md` if missing.
- [ ] Run the `solera-init` Step 3 scaffolding check idempotently for any other subdirs still missing (`.solera/roles/`, `.solera/personas/`, etc.).

### 6. Rebuild indexes

- [ ] Regenerate `.solera/roles/_index.md` — active indented by parent chain; deprecated flat; archived omitted.
- [ ] Regenerate `.solera/personas/_index.md` — group active Personas by their Role (header line per Role).
- [ ] Regenerate `.solera/journeys/_index.md` — group active Journeys by their new `walks` Role.
- [ ] Regenerate `.solera/narratives/_index.md` — group active Narratives by `in_journey` (or "Loose") as before.

### 7. Write the migration log

- [ ] Create `.solera/MIGRATION-v4-to-v5.md` with:
  - Date.
  - Per-persona decision: `{id}` → `promoted to Role` / `kept as Persona under {role}` / `split`.
  - Per-journey `walks` adjustment.
  - Per-narrative `about` split.
  - Any orphans still pending human repair (links to the integrity banners in the Actors canvas).

### 8. Wrap-up

- [ ] Emit a summary to the user:
  > "Migration complete. `{N_role}` Roles promoted, `{N_persona}` Personas kept, `{N_journey}` Journeys re-stamped, `{N_narrative}` Narratives re-stamped. See `.solera/MIGRATION-v4-to-v5.md` for the full decision log. Open the Actors canvas to verify the new Role tree."
- [ ] Suggest the user commit the whole migration as a single atomic commit: `git add .solera && git commit -m "chore(solera): migrate v4 workspace to v5 (Role)"`.

## Idempotency & re-run

Every mutating step checks "already migrated" state by reading the destination file and skipping if the expected shape is present. A second run after a partial failure picks up exactly where the previous run stopped.

## Error Handling

| Failure | Condition | Recovery | Exit |
|---|---|---|---|
| Dirty working tree | `git status --porcelain` non-empty | Ask user to commit/stash; halt | Halt |
| No `.solera/personas/` | No Personas to migrate | Skip Steps 2–4; still seed the new structure | Continue |
| User cancels midway | `AskUserQuestion` interrupted | Record the decisions made so far; write a partial log; mark the workspace as "mid-migration" | Exit gracefully |
| Broken references after migration | Some `walks`/`about_roles` points at a non-existent Role | Record in the log with `needs_human_repair: true`; do NOT auto-create Roles silently | Continue with warning |

## Completion Checklist

- [ ] `.solera/roles/*.md` created for every structural Persona
- [ ] Every remaining `.solera/personas/*.md` has a valid `role:` frontmatter field
- [ ] Every `.solera/journeys/*.md` has `walks:` referencing a Role id
- [ ] Every `.solera/narratives/*.md` has `about_roles:` (1+) instead of `about:`
- [ ] `.solera/MIGRATION-v4-to-v5.md` written
- [ ] Indexes regenerated for all four entity directories
- [ ] User advised to commit the migration as a single atomic commit
