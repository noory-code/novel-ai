---
name: solera-write-role
user-invocable: true
description: Draw, update, deprecate, or archive a Role — a structural user class this service is for (admin, fan, hero, 3rd-party, etc.).
metadata:
  version: "1.0.0"
  category: writing
  type: unit
  style: procedural
  triggers: [write a role, draw a role, add a role, update role, deprecate role, archive role, add admin role, add user role]
  uses: []
---

<!-- SSOT: ../../docs/reference/axes-and-status.md — Role status values (`active`/`deprecated`/`archived`) and the `parent` cycle/self/archive rules live there -->

# Writing Role

> A Role is a living, structural class of user the service is for.
> Humans draw Roles; AI proposes and questions, never decides alone.
> Roles never end — they evolve as the audience changes.

## Philosophy

Roles belong to the **Living Axis** — alongside Identity, Personas, Journeys, Narratives, and Concepts. They are the **primary tree around Identity** on the Actors canvas. Examples: `admin`, `general-user`, `fan`, `hero`, `3rd-party`. A Role describes *the position someone occupies when they use the service* — not a specific named individual.

A Role holds:

- **Description** — one paragraph: who this Role is, in the most essential terms.
- **Context** — when/where this Role shows up (optional).
- **Parent** — another Role this one sits inside (e.g., `fan` under `general-user`).

A Role **may** later anchor individual **Personas** (e.g., "성덕 30대 Alice" as a concrete archetype of the `fan` Role). Personas reference their Role via `role: {role_id}`. Early-stage projects typically have Roles only, no Personas — that's fine.

See also [`solera-write-persona`](../solera-write-persona/SKILL.md) (for individual archetypes under a Role), [`solera-write-journey`](../solera-write-journey/SKILL.md) (a Journey `walks` a Role), and [`solera-write-narrative`](../solera-write-narrative/SKILL.md) (a Narrative `about_roles` one or more Roles).

This skill handles four modes:

| Mode | When |
|------|------|
| `create` | Drafting a brand-new Role |
| `update` | Revising Description / Context / Related on an existing one |
| `deprecate` | Role is fading from the project's audience but still referenced |
| `archive` | Role is fully retired and should drop from the active index |

## Prerequisites

- `{project_path}/.solera/identity/mission.md` should exist (the project knows what it stands for before defining who it's for).
  - If not: ask the user to invoke `solera-write-identity` first.
- `{project_path}/.solera/roles/` directory (created by `solera-init` or on first `create`).

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas |
| **mode** | Y | `create` \| `update` \| `deprecate` \| `archive` | create |
| **role_id** | Y | Kebab-case ID | fan |
| **role_name** | N | Human-readable name (defaults to title-cased id) | Fan |
| **parent** | N | Parent Role id; omit or `null` for a top-level Role | general-user |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create | Role file | `{project_path}/.solera/roles/{role_id}.md` | Final |
| Wrap-up | Updated index | `{project_path}/.solera/roles/_index.md` | Final |

## Procedure

### 1. Setup

- [ ] Confirm `{project_path}/.solera/identity/mission.md` exists. If missing, stop and advise `solera-write-identity`.
- [ ] Ensure `{project_path}/.solera/roles/` exists; create if missing.
- [ ] Ensure `{project_path}/.solera/roles/_index.md` exists; if missing, scaffold from [assets/_index-template.md](assets/_index-template.md).
- [ ] Resolve role file path: `{project_path}/.solera/roles/{role_id}.md`.
- [ ] Branch by `mode`:
  - `create` — file must **not** exist → proceed to Create.
  - `update` / `deprecate` / `archive` — file **must** exist → proceed.
  - Violation → stop with a clear error.

### 2. Create (mode = create)

- [ ] Read [assets/role-template.md](assets/role-template.md).

- [ ] **Ask the human for the Description** (blocking). Prompt in the user's language:
  > "Who is this Role? One paragraph — the position someone occupies when they use the service. Not an individual."
  - Reject empty / placeholder responses.
  - If the human replies "just write it" / "you decide" / equivalent: surface 2–3 candidate descriptions based on observed artifacts (identity, existing Roles) and have the human pick / revise. Never invent unilaterally.

- [ ] **Ask the human for Context** (optional, blocking with skip):
  > "When / where does this Role show up? Skip if not applicable."

- [ ] **Offer AI observations before writing** (advisory, non-blocking):
  - Scan `roles/*.md` for similar existing Roles (possible overlap).
  - Scan `identity/*.md` for role-like references already captured.
  - Present findings as:
    ```
    Observations (for your consideration — not decisions):
    - Possibly overlaps with Role "{other_id}" on {reason}.
    - Identity already mentions: "{snippet}".
    ```
  - Ask: "Does this change how you'd like to draw this Role?"

- [ ] **Resolve `parent`** (AI proposes; human decides):
  - If invocation passed `parent`: validate exists + is `active`. On failure, halt.
  - Otherwise: infer a candidate from existing Roles whose description subsumes the new one. Examples: new `vip-fan` under existing `fan`.
  - Present the candidate as a proposal:
    > "`{role_id}` looks like it sits under `{candidate_id}`. Confirm, pick a different parent, or keep it top-level?"
  - Human chooses: accept candidate / specify different / explicit `null`.
  - **Reject cycles and self-parenting** per axes-and-status.md.

- [ ] Write the Role file using the template, filling:
  - Frontmatter: `id`, `kind: role`, `name`, `status: active`, `created: {today in YYYY-MM-DD}`.
  - `parent: {parent_id}` — include only if a parent was resolved; **omit the line entirely** for top-level Roles (don't write `parent: null`).
  - `# Description` and `# Context` (omit Context section if human skipped).
  - Keep the `## Workflow` section from the template intact.

- [ ] Proceed to Wrap-up.

### 3. Update (mode = update)

- [ ] Read the existing Role file.
- [ ] Ask the human what to change. Offer a small menu:
  - Description
  - Context
  - **Parent** (re-home under different parent or promote to top-level)
- [ ] For each chosen section, show current content, ask for new content, replace after confirmation.
- [ ] **When `parent` is chosen**: same cycle/self/archive validation as the Concept path (axes-and-status.md → `parent`).
- [ ] Append `<!-- updated: YYYY-MM-DD -->` at the top of each edited section.
- [ ] Proceed to Wrap-up.

### 4. Deprecate (mode = deprecate)

- [ ] Ask the human for a one-line reason: "Why is this Role being deprecated?"
- [ ] Set `status: deprecated`.
- [ ] Prepend a `> ⚠️ Deprecated {date} — {reason}` block below the frontmatter.
- [ ] Keep all other content (history is preserved).
- [ ] Proceed to Wrap-up.

### 5. Archive (mode = archive)

- [ ] Ask the human to confirm. Warn: Personas with `role: {role_id}`, Journeys that `walks: {role_id}`, and Narratives with this Role in `about_roles` will surface as `inactive_*_ref` integrity issues on the Actors canvas. The human can choose to re-home each dependent later.
- [ ] Set `status: archived`.
- [ ] Proceed to Wrap-up.

### 6. Wrap-up

- [ ] Update `{project_path}/.solera/roles/_index.md`:
  - `active` section lists all `active` Roles, indented by `parent` chain (top-level at indent 0; children +2 spaces per depth; alphabetical within sibling groups).
  - `deprecated` section flat.
  - Archived files are **not** listed (file remains on disk).
  - Orphans (parent missing or non-`active`) render at indent 0 with `— ⚠️ orphan` marker.
- [ ] Emit a short summary to the user:
  - For `create`: `Role {id} drawn{parent_note}. Index updated.`
  - For `update`: `Role {id} updated: {sections changed}.`
  - For `deprecate`/`archive`: `Role {id} now {status}.`
- [ ] Append a **next-step hint** on `create` (omit on `update`/`deprecate`/`archive`):
  > "Next: add more Roles with `solera-write-role`, or run `solera-write-journey` to describe what `{role_id}` walks, or `solera-write-narrative` for user stories about them. Individual archetypes come later via `solera-write-persona role:{role_id}` once you deepen this Role."

## Human–AI Protocol

This skill belongs to the same Moment 1 (drawing the Living axis) family as `solera-write-concept` / `solera-write-persona`. The collaboration rule is identical:

| AI does | AI does not |
|---------|-------------|
| Ask clarifying questions | Invent the audience |
| Offer observations from identity / other Roles | Merge / split Roles unilaterally |
| Rephrase for clarity, with human approval | Mark anything as final without human confirmation |
| Propose a `parent` based on observed overlap | Write `parent` silently |
| Update the index and file structure | Decide a Role is deprecated / archived without the human asking |

If the human says "just write it", the AI surfaces a proposed draft and waits for confirmation — the file is the human's drawing.

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| Missing identity | `mission.md` absent | Ask user to run `solera-write-identity` | Halt |
| Create conflict | File exists in `create` mode | Offer `update` or archive/create-new | Halt until mode resolved |
| Update target missing | File absent in `update`/`deprecate`/`archive` | Offer `create` mode | Halt until mode resolved |
| Unknown parent | `parent` references a non-existent Role | List available; halt | Halt until fixed |
| Inactive parent | `parent` exists but is `deprecated`/`archived` | Ask for different parent (or top-level) | Halt until fixed |
| Self-parent | `parent == role_id` | Reject | Halt until fixed |
| Parent cycle | Setting parent would loop | Show chain; reject | Halt until fixed |
| Role archived with dependents | Personas/Journeys/Narratives still reference this Role | Warn the human; do not auto-cascade archive | Continue with warning |

## Completion Checklist

- [ ] Role file at expected path with all required sections
- [ ] Frontmatter `id`, `kind`, `name`, `status`, `created` present and correct
- [ ] Description provided by human (not AI-generated)
- [ ] `_index.md` reflects the file's current status
- [ ] Summary message delivered to user
