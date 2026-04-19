---
name: solera-write-narrative
user-invocable: true
description: Draw, update, deprecate, or archive a Narrative — a "As a / I want / so that" statement (or JTBD / scenario) that proposes Concepts. Distinct from Solera's Time-bound Story (work item).
metadata:
  version: "2.0.0"
  category: writing
  type: unit
  style: procedural
  triggers: [write a narrative, draw a narrative, add a narrative, write a user story, JTBD, propose concept from narrative, update narrative, deprecate narrative, archive narrative]
  uses: []
---

<!-- SSOT: ../../docs/reference/axes-and-status.md — Narrative status values (`active`/`deprecated`/`archived`), the `about_roles` / `about_personas` / `in_journey` / `proposes` relations, and transitions live there -->

# Writing Narrative

> A Narrative is a living, "As a {Role} I want {goal} so that {benefit}" statement (or JTBD / scenario form).
> Humans write Narratives; AI proposes and questions, never decides alone.
> Narratives are **upstream of Concepts** — they may `proposes:` Concepts, either by human authorship or via the Actors canvas's "Propose as Concept" action.

## Philosophy

Narratives belong to the **Living Axis** — alongside Identity, Roles, Personas, Journeys, and Concepts. They are the explicit articulation of "what should the service do, from the user's standpoint." The flow is:

```
Role ───► Journey (steps) ───► Narrative ───► Concept (drafted, human-reviewed)
```

A Narrative holds:

- **Statement** — the literal sentence in the chosen `form` (`user_story` / `jtbd` / `scenario`).
- **Context** — why this matters; what state the Role (or specific Persona) is in.
- **Acceptance Cues** — observable signs the system delivered the benefit. **Not acceptance criteria** — those belong on the Story (Time-bound work item) that this Narrative may eventually inspire.
- **Related** — `about_roles` (1+ required — the structural anchor), optional `about_personas` (concrete Persona archetypes), optional `in_journey` Journey, optional `proposes` Concepts, plus free-form references.

### Narrative vs Solera's Time-bound Story

Solera already has a **Story** work item (Time-bound axis: `solera-write-story`). It is a unit of executable work decomposed into Action Items, with `contributes_to: [concept_id]`. **A Narrative is not that.**

| | Narrative (this skill) | Story (`solera-write-story`) |
|--|---|---|
| Axis | Living | Time-bound |
| Lifecycle | Never ends; evolves with the audience | Starts, runs, completes (✅), terminal |
| Shape | "As a / I want / so that" sentence with cues | Acceptance criteria + Action Items table |
| Status | `active` / `deprecated` / `archived` | `⏳` / `🔄` / `✅` / `⏸️` / `❌` |
| Owns | The framing of the user-side need | The execution of the work that satisfies it |
| `proposes:` Concepts | Yes (informational; canvas can auto-fill) | No — Stories `contributes_to:` existing Concepts |

Folder: `narratives/` (Living) vs `stories/` (Time-bound). Frontmatter: `kind: narrative` vs `_story.md`. They never collide in code or in the file tree.

### "Propose as Concept" interaction

The Actors canvas exposes a "Propose as Concept" action on each Narrative. When a human clicks it, the canvas POSTs to the Solera MCP server's `/api/concept/propose-from-narrative` endpoint, which writes a **stub** Concept whose `# Intent` is explicitly flagged "needs human review per solera-write-concept Moment 1 rule" and adds the new concept_id to this Narrative's `proposes:` list. The human then runs `solera-write-concept` in `update` mode to fill the real Intent. **No Concept is finalized without the human writing its Intent.**

## Prerequisites

- `{project_path}/.solera/roles/_index.md` exists with at least one active Role (since `about_roles` requires 1+ active Role).
  - If not: ask the user to invoke `solera-write-role` first.
- `{project_path}/.solera/narratives/` directory (created by `solera-init` or on first `create`).

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas |
| **mode** | Y | `create` \| `update` \| `deprecate` \| `archive` | create |
| **narrative_id** | Y | Kebab-case ID | buyer-finds-trusted-cafe |
| **form** | N (default `user_story`) | `user_story` \| `jtbd` \| `scenario` | jtbd |
| **about_roles** | Y (in `create`) | List of Role ids this Narrative concerns (1+ required) | [fan] |
| **about_personas** | N | Optional list of Persona ids for concrete archetype anchoring | [alice] |
| **in_journey** | N | Journey id this Narrative anchors to | first-time-checkout |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create | Narrative file | `{project_path}/.solera/narratives/{narrative_id}.md` | Final |
| Wrap-up | Updated index | `{project_path}/.solera/narratives/_index.md` | Final |

## Procedure

### 1. Setup

- [ ] Confirm `{project_path}/.solera/roles/_index.md` exists and contains ≥1 active Role. If not, stop and advise `solera-write-role`.
- [ ] Ensure `{project_path}/.solera/narratives/` exists; create if missing.
- [ ] Ensure `{project_path}/.solera/narratives/_index.md` exists; if missing, scaffold from [assets/_index-template.md](assets/_index-template.md).
- [ ] Resolve narrative file path: `{project_path}/.solera/narratives/{narrative_id}.md`.
- [ ] Branch by `mode`:
  - `create` — file must **not** exist → proceed to Create.
  - `update` / `deprecate` / `archive` — file **must** exist → proceed.
  - Violation → stop with a clear error.

### 2. Create (mode = create)

- [ ] Read [assets/narrative-template.md](assets/narrative-template.md).

- [ ] **Resolve `form`** (default `user_story`):
  - Prompt-templates change by form:
    - `user_story` → "As a {Persona}, I want {goal} so that {benefit}."
    - `jtbd` → "When {situation}, I want {motivation}, so I can {outcome}."
    - `scenario` → 2–3 sentence prose scenario.
  - Confirm with the human or accept the argument.

- [ ] **Resolve `about_roles`** (required, 1+ Roles):
  - If `about_roles` argument provided: validate every named Role exists + is `active`. On any failure, halt with the list of active Roles.
  - Otherwise ask: "Which Role(s) is this Narrative about? (list one or more active Roles — these are the structural audience anchors)"
  - If the human names a Role that is not yet drawn: stop and advise `solera-write-role`.

- [ ] **Resolve `about_personas`** (optional, 0+ Personas):
  - If `about_personas` provided: validate every named Persona exists + is `active` + its `role` is contained in `about_roles` (a Persona can only concretise a Narrative about its own Role).
  - Otherwise ask (with explicit skip): "Any specific Persona archetypes this Narrative is about? Skip if the Role-level audience is enough."

- [ ] **Resolve `in_journey`** (optional):
  - If argument provided: validate exists + is `active`.
  - Otherwise: ask the human (with skip option). If they name a Journey that does not exist: offer to skip or to draw the Journey first via `solera-write-journey`.

- [ ] **Ask the human for the Statement** (blocking):
  - Show the form-specific prompt template above.
  - Reject empty / placeholder responses.
  - AI **must not** invent the Statement; only refine wording with approval.

- [ ] **Ask the human for Context** (blocking):
  > "Why does this matter? What state is the Persona in?"
  - Reject placeholder responses.

- [ ] **Ask the human for Acceptance Cues** (blocking, list — at least one):
  > "What observable signs would tell you the system delivered the benefit?"
  - These are **not** acceptance criteria for a Story. Frame them as cues / signals.
  - Reject empty list.

- [ ] **Offer AI observations before writing** (advisory):
  - Scan `narratives/*.md` for Narratives with overlapping Statements or shared `about` — possible duplicates.
  - Scan `concepts/*.md` for Concepts that this Narrative might propose (matching keywords from Statement / Context).
  - Present findings as:
    ```
    Observations (for your consideration — not decisions):
    - Possibly overlaps with Narrative "{other_id}".
    - Concepts this Narrative might propose: {concept_ids}.
    ```
  - Ask: "Should `proposes:` start with any of these Concepts, or stay empty?"

- [ ] **Resolve `proposes`** (optional, 0+ Concepts):
  - If the human names existing Concepts: validate each exists + is `active`.
  - If the human asks to draft new Concepts now: instruct them to use the Actors canvas's "Propose as Concept" action OR to invoke `solera-write-concept` directly with `mode: create`.
  - **Never auto-finalize a new Concept from this skill** — that path goes through the Actors canvas with the stub-Intent guard.

- [ ] Write the Narrative file using the template, filling:
  - Frontmatter: `id`, `kind: narrative`, `form`, `status: active`, `created: {today in YYYY-MM-DD}`, `about_roles: [...]`, optional `about_personas: [...]`, optional `in_journey`, optional `proposes: [...]`.
  - All sections from human input.
  - Keep the `## Workflow` section from the template intact.

- [ ] Proceed to Wrap-up.

### 3. Update (mode = update)

- [ ] Read the existing Narrative file.
- [ ] Ask the human what to change. Offer a small menu:
  - Statement (and optionally `form`)
  - Context
  - Acceptance Cues
  - Related (`about_roles` / `about_personas` / `in_journey` / `proposes` / free-form)
- [ ] For each chosen section, show current content, ask for new content, replace after confirmation.
- [ ] **When `about_roles` is changed**: validate new Roles exist + `active`; reject empty list.
- [ ] **When `about_personas` is changed**: validate Personas exist + `active` + their `role` is in `about_roles`.
- [ ] **When `in_journey` is changed**: validate exists + `active`; allow `null` to detach.
- [ ] **When `proposes` is changed**: validate every Concept exists + `active`; allow `[]` to clear.
- [ ] Append `<!-- updated: YYYY-MM-DD -->` at the top of each edited section.
- [ ] Proceed to Wrap-up.

### 4. Deprecate (mode = deprecate)

- [ ] Ask the human for a one-line reason.
- [ ] Set `status: deprecated`.
- [ ] Prepend `> ⚠️ Deprecated {date} — {reason}` below frontmatter.
- [ ] Keep all other content intact.
- [ ] Proceed to Wrap-up.

### 5. Archive (mode = archive)

- [ ] Ask the human to confirm. Note: any Concepts in `proposes` are not affected — they continue independently.
- [ ] Set `status: archived`.
- [ ] Proceed to Wrap-up.

### 6. Wrap-up

- [ ] Update `{project_path}/.solera/narratives/_index.md`:
  - `active` section: list all `active` Narratives, **grouped by `in_journey`** (Journey id, then a "Loose Narratives" group for those without `in_journey`). Within each group, alphabetical by id.
  - `deprecated` section flat.
  - Archived files are **not** listed (file remains on disk).
  - Orphans (named Persona / Journey deprecated/archived) render with `— ⚠️ orphan` marker.
- [ ] Emit a short summary to the user:
  - For `create`: "Narrative `{id}` written ({form}, about_roles: {about_roles}{about_personas_note}{journey_note}{proposes_note}). Index updated."
  - For `update`: "Narrative `{id}` updated: {sections changed}."
  - For `deprecate`/`archive`: "Narrative `{id}` now {status}."
- [ ] Append a **next-step hint** on `create` (omit on `update`/`deprecate`/`archive`):
  > "Next: open the Actors canvas and click **Propose as Concept** on this Narrative — it writes a stub Concept flagged 'needs human review', which you then fill via `solera-write-concept` in `update` mode. Or invoke `solera-write-concept` directly if the Concept already exists."

## Human–AI Protocol

This skill belongs to the same Moment 1 family as `solera-write-concept`, `solera-write-persona`, and `solera-write-journey`.

| AI does | AI does not |
|---------|-------------|
| Ask clarifying questions for each section | Invent the Statement, Context, or Acceptance Cues |
| Offer observations from sibling Narratives / candidate Concepts | Auto-add Concepts to `proposes` |
| Refine wording with human approval | Mark anything as final without confirmation |
| Validate `about` / `in_journey` / `proposes` references | Silently drop a reference that has gone stale |
| Direct the human to the Actors canvas for "Propose as Concept" workflow | Finalize a Concept from this skill |

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| No active Roles | `roles/_index.md` empty | Advise `solera-write-role` first | Halt |
| Empty `about_roles` | No Roles named | Reject; require ≥1 active Role | Halt until fixed |
| Unknown `about_roles` Role | Named Role missing or non-`active` | List active Roles; halt | Halt until fixed |
| `about_personas` Role mismatch | Persona's `role` not in `about_roles` | Reject; suggest adding the Role to `about_roles` or removing the Persona | Halt until fixed |
| Unknown `in_journey` Journey | Named Journey missing or non-`active` | Offer skip or draw the Journey first | Halt until chosen |
| Unknown Concept in `proposes` | Named Concept missing or non-`active` | List active Concepts; halt | Halt until fixed |
| Create conflict | File exists in `create` mode | Offer `update` or archive/create-new | Halt until mode resolved |
| Update target missing | File absent in `update`/`deprecate`/`archive` | Offer `create` mode | Halt until mode resolved |
| Empty Acceptance Cues | List has zero entries | Reject; require ≥1 cue | Halt until fixed |
| Persona / Journey deprecated after the fact | Reference now points at a non-`active` item | Surface as orphan in `_index.md`; do not auto-mutate the Narrative | Continue with warning |

## Completion Checklist

- [ ] Narrative file at expected path with all required sections
- [ ] Frontmatter `id`, `kind`, `form`, `status`, `created`, `about` present and correct
- [ ] Statement, Context, and Acceptance Cues provided by human (not AI-generated)
- [ ] `about` is a non-empty list of active Personas
- [ ] `_index.md` reflects the file's current status
- [ ] Summary message delivered to user
