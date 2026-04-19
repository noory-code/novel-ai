---
name: solera-write-persona
user-invocable: true
description: Draw, update, deprecate, or archive a Persona — a kind of user the service is for.
metadata:
  version: "2.0.0"
  category: writing
  type: unit
  style: procedural
  triggers: [write a persona, draw a persona, add a persona, update persona, deprecate persona, archive persona]
  uses: []
---

<!-- SSOT: ../../docs/reference/axes-and-status.md — Persona status values (`active`/`deprecated`/`archived`) and transitions live there -->

# Writing Persona

> A Persona is a living, evolving description of someone the service is for.
> Humans draw Personas; AI proposes and questions, never decides alone.
> Personas never end — they evolve as understanding deepens or as the audience changes.

## Philosophy

Personas belong to the **Living Axis** — alongside Identity, Roles, Journeys, Narratives, and Concepts. A Persona is a **concrete archetype under a Role** — "성덕 30대 Alice" as a representative of the `fan` Role, for instance. Roles describe structural audience classes; Personas add the named, textured flavour for the rare cases where that concreteness matters. A Role can exist with zero Personas (most early-stage projects work that way).

Every Persona **must declare its Role** via the required `role` frontmatter field. If you're reaching for Persona before you have any Role defined, start with [`solera-write-role`](../solera-write-role/SKILL.md) first.

A Persona holds:

- **Identity** — who they are in one paragraph (role, demographic shorthand, context).
- **Goals** — what they are trying to accomplish.
- **Pains** — what hurts them now.
- **Triggers** — events that bring them to a service like ours.
- **Quotes** — verbatim or composite (clearly marked) sentences in their voice.
- **Channels** — where we reach them (optional).
- **Related** — Journeys they walk, Narratives about them, Concepts they pressure.

A Persona may optionally declare a `parent` — another Persona it sits inside (e.g., "VIP buyer" under "buyer"). See [axes-and-status.md → `parent`](../../docs/reference/axes-and-status.md#parent-concept--concept-persona--persona-journey--journey) for cycle/self-parent/archive rules.

This skill handles four modes:

| Mode | When |
|------|------|
| `create` | Drafting a brand-new Persona |
| `update` | Revising any field on an existing one |
| `deprecate` | Persona is fading from the project's audience but still referenced |
| `archive` | Persona is fully retired and should drop from the active index |

## Prerequisites

- `{project_path}/.solera/identity/mission.md` should exist (project knows what it stands for before defining who it's for).
  - If not: ask the user to invoke `solera-write-identity` first.
- `{project_path}/.solera/roles/` contains **at least one active Role** (Personas must be archetypes of a Role).
  - If not: stop and advise `solera-write-role` first.
- `{project_path}/.solera/personas/` directory (created by `solera-init` or on first `create`).

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas |
| **mode** | Y | `create` \| `update` \| `deprecate` \| `archive` | create |
| **persona_id** | Y | Kebab-case ID | small-cafe-owner |
| **role** | Y (in `create`) | Role id this Persona is an archetype of — must be an active Role | fan |
| **persona_name** | N | Human-readable name or archetype (defaults to title-cased id) | Small Cafe Owner |
| **parent** | N | Parent Persona id; omit or `null` for a top-level Persona within its Role | buyer |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create | Persona file | `{project_path}/.solera/personas/{persona_id}.md` | Final |
| Wrap-up | Updated index | `{project_path}/.solera/personas/_index.md` | Final |

## Procedure

### 1. Setup

- [ ] Confirm `{project_path}/.solera/identity/mission.md` exists. If missing, stop and ask user to run `solera-write-identity`.
- [ ] Confirm `{project_path}/.solera/roles/_index.md` exists and contains ≥1 active Role. If not, stop and advise `solera-write-role`.
- [ ] Ensure `{project_path}/.solera/personas/` exists; create if missing.
- [ ] Ensure `{project_path}/.solera/personas/_index.md` exists; if missing, scaffold from [assets/_index-template.md](assets/_index-template.md).
- [ ] Resolve persona file path: `{project_path}/.solera/personas/{persona_id}.md`.
- [ ] Branch by `mode`:
  - `create` — file must **not** exist → proceed to Create.
  - `update` / `deprecate` / `archive` — file **must** exist → proceed.
  - Violation → stop with a clear error.

### 2. Create (mode = create)

- [ ] Read [assets/persona-template.md](assets/persona-template.md).

- [ ] **Resolve `role`** (required, exactly one Role):
  - If `role` argument provided: validate the named Role exists + is `active`. On failure, halt with the list of active Roles.
  - Otherwise: ask the human:
    > "Which Role is this Persona an archetype of? (exactly one — Personas must belong to a Role)"
  - If the human names a Role that is not yet drawn: stop and advise `solera-write-role` first.

- [ ] **Ask the human who this Persona is** (blocking). Prompt in the user's language:
  > "Who is this Persona? One paragraph — their role, situation, and why they care about a service like yours."
  - Reject empty, single-word, or obvious placeholder responses. Ask again with a concrete example to prime.
  - If the human replies with "just write it" / "you decide" / equivalent: **do not proceed**. Respond:
    > "I can't invent who your user is — that's the one thing only you know. But I can suggest 2–3 candidate descriptions based on Identity and existing Personas, and you pick or reject. Shall I?"
    Produce candidates only from observed artifacts (identity, existing Personas, Narratives). Human must choose or reword one; otherwise loop.
  - AI **must not** invent the Identity paragraph; only refine wording after the human proposes.

- [ ] **Offer AI observations before writing the rest** (advisory, non-blocking):
  - Scan `personas/*.md` for already-active Personas with overlapping descriptions or quotes.
  - Scan `identity/*.md` for any persona references already captured during identity setup.
  - Scan `narratives/*.md` for `about: [{persona_id}]` references that imply who the audience already is.
  - Present findings as:
    ```
    Observations (for your consideration — not decisions):
    - Possibly overlaps with Persona "{other_id}" on {reason}.
    - Identity already mentions: "{snippet}".
    - Narratives that may belong to this Persona: {narrative_id}.
    ```
  - Ask the human: "Does any of this change how you'd like to draw this Persona?"

- [ ] **Ask the human for Goals, Pains, Triggers, Quotes** (blocking, but offer fast-fill):
  - Prompt one cluster at a time. Empty answers are allowed for any cluster except Goals (which is core).
  - For Quotes: offer "verbatim from a real interview" / "composite that captures the voice" / "skip" — and **mark each quote with its kind**.

- [ ] **Resolve `parent`** (AI proposes; human decides):
  - If invocation passed `parent`: validate exists + is `active`. On failure, halt.
  - Otherwise: infer a candidate from the new Persona's Identity + existing Personas. Examples:
    - Same role, narrower context → suggest the broader one as parent (e.g. new `vip-buyer` under existing `buyer`).
    - Same role, different demographic → no parent (peers).
  - Present the candidate as a proposal:
    > "이 Persona가 `{candidate_id}` 아래에 들어가는 게 자연스러워 보입니다. 맞나요? 아니면 다른 parent, 아니면 top-level로 두시겠어요?"
  - Human chooses: accept candidate / specify different / explicit `null`.
  - **Reject cycles and self-parenting** per axes-and-status.md.

- [ ] Write the Persona file using the template, filling:
  - Frontmatter: `id`, `kind: persona`, `name`, `status: active`, `created: {today in YYYY-MM-DD}`, `role: {role_id}`.
  - `parent: {parent_id}` — include only if a parent was resolved; **omit the line entirely** for top-level Personas (don't write `parent: null`).
  - All sections from human input (or omit empty sections rather than leave dangling placeholders).
  - Keep the `## Workflow` section from the template intact.

- [ ] Proceed to Wrap-up.

### 3. Update (mode = update)

- [ ] Read the existing Persona file.
- [ ] Ask the human what to change. Offer a small menu:
  - Identity (the opening paragraph)
  - Goals
  - Pains
  - Triggers
  - Quotes
  - Channels
  - Related (Journeys / Narratives / Concepts cross-links)
  - **Parent** (re-home under different parent or promote to top-level)
- [ ] For each chosen section, show current content, ask for new content, replace after confirmation.
- [ ] **When `parent` is chosen for editing**: same validation as Concept (axes-and-status.md → `parent`).
- [ ] Append `<!-- updated: YYYY-MM-DD -->` at the top of each edited section.
- [ ] Proceed to Wrap-up.

### 4. Deprecate (mode = deprecate)

- [ ] Ask the human for a one-line reason: "Why is this Persona being deprecated?"
- [ ] Set `status: deprecated`.
- [ ] Prepend a `> ⚠️ Deprecated {date} — {reason}` block below the frontmatter.
- [ ] Keep all other content (history is preserved).
- [ ] Proceed to Wrap-up.

### 5. Archive (mode = archive)

- [ ] Ask the human to confirm. Note: Journeys that `walks` this Persona become orphans.
- [ ] Set `status: archived`.
- [ ] Proceed to Wrap-up.

### 6. Wrap-up

- [ ] Update `{project_path}/.solera/personas/_index.md`:
  - `active` section lists all `active` Personas, indented by `parent` chain (top-level at indent 0; children +2 spaces per depth; alphabetical within sibling groups).
  - `deprecated` section flat (hierarchy less meaningful for fading items).
  - Archived files are **not** listed (file remains on disk).
  - Orphans (parent missing or non-`active`) render at indent 0 with `— ⚠️ orphan` marker.
- [ ] Emit a short summary to the user:
  - For `create`: "Persona `{id}` drawn{parent_note}. Index updated."
  - For `update`: "Persona `{id}` updated: {sections changed}."
  - For `deprecate`/`archive`: "Persona `{id}` now {status}."
- [ ] Append a **next-step hint** on `create` (omit on `update`/`deprecate`/`archive`):
  > "Next: `solera-write-narrative` with `about_personas: [{persona_id}]` for a user story that names this specific archetype. For Journeys, remember they `walks` the Role — reference this Persona via `walked_by` when the Journey is a concrete case for `{persona_id}`. Open the Actors canvas to see the placement."

## Human–AI Protocol

This skill belongs to the same Moment 1 (drawing the Living axis) family as `solera-write-concept`. The collaboration rule is identical:

| AI does | AI does not |
|---------|-------------|
| Ask clarifying questions | Invent who the user is |
| Offer observations from identity / other Personas / Narratives | Merge / split Personas unilaterally |
| Rephrase for clarity, with human approval | Mark anything as final without human confirmation |
| Propose a `parent` based on observed overlap | Write `parent` silently |
| Update the index and file structure | Decide that a Persona is deprecated / archived without the human asking |

If the human says "just write it", the AI surfaces a proposed draft and waits for confirmation — the file is the human's drawing.

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| Missing identity | `mission.md` absent | Ask user to run `solera-write-identity` | Halt |
| Create conflict | File exists in `create` mode | Offer `update` or archive/create-new | Halt until mode resolved |
| Update target missing | File absent in `update`/`deprecate`/`archive` | Offer `create` mode | Halt until mode resolved |
| Unknown parent | `parent` references a non-existent Persona | List available; halt | Halt until fixed |
| Inactive parent | `parent` exists but is `deprecated`/`archived` | Ask for different parent (or top-level) | Halt until fixed |
| Self-parent | `parent == persona_id` | Reject | Halt until fixed |
| Parent cycle | Setting parent would loop | Show chain; reject | Halt until fixed |
| Deprecated Persona still walked | A `journeys/*.md` lists `walks: {persona_id}` | Warn the human; do not auto-deprecate the Journeys | Continue with warning |

## Completion Checklist

- [ ] Persona file at expected path with all required sections
- [ ] Frontmatter `id`, `kind`, `name`, `status`, `created` present and correct
- [ ] Identity paragraph provided by human (not AI-generated)
- [ ] `_index.md` reflects the file's current status
- [ ] Summary message delivered to user
