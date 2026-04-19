---
name: solera-write-journey
user-invocable: true
description: Draw, update, deprecate, or archive a Journey — the sequence of steps a Persona walks through when interacting with the service.
metadata:
  version: "1.0.0"
  category: writing
  type: unit
  style: procedural
  triggers: [write a journey, draw a journey, add a journey, update journey, deprecate journey, archive journey, user journey]
  uses: []
---

<!-- SSOT: ../../docs/reference/axes-and-status.md — Journey status values (`active`/`deprecated`/`archived`), the `walks` relation, and transitions live there -->

# Writing Journey

> A Journey is a living sequence of steps a Persona walks.
> Humans draw Journeys; AI proposes and questions, never decides alone.
> Journeys never end — they evolve as the Persona's experience changes.

## Philosophy

Journeys belong to the **Living Axis** — alongside Identity, Personas, Narratives, and Concepts. They are **upstream of Concepts**: a Journey reveals which steps the service must support, which pressures Concept design.

A Journey holds:

- **Trigger** — what kicks off this journey for the Persona.
- **Steps** — a markdown table: `# | Stage | Step | Touchpoint | Emotion | Pain`.
- **Outcome** — what success looks like for the Persona at the end.
- **Related** — back-link to the Persona that walks it; Narratives anchored to it; Concepts touched by its steps.

Steps stay **inside the table**, not as separate files. A Journey is read-mostly; the Service canvas renders it as a swimlane row.

A Journey is always walked by **exactly one** Persona (`walks: {persona_id}`, required). Multi-persona journeys must be split into one Journey per Persona — this keeps swimlane visualization unambiguous.

A Journey may optionally declare a `parent` — a variant journey under a base journey (e.g., "first-time onboarding" under "onboarding"). See [axes-and-status.md → `parent`](../../docs/reference/axes-and-status.md#parent-concept--concept-persona--persona-journey--journey) for cycle/self-parent/archive rules.

This skill handles four modes:

| Mode | When |
|------|------|
| `create` | Drafting a brand-new Journey |
| `update` | Revising Trigger / Steps / Outcome / Related on an existing one |
| `deprecate` | Journey is fading from the project's flow but still referenced |
| `archive` | Journey is fully retired and should drop from the active index |

## Prerequisites

- `{project_path}/.solera/personas/_index.md` exists with at least one active Persona (since `walks` is required).
  - If not: ask the user to invoke `solera-write-persona` first.
- `{project_path}/.solera/journeys/` directory (created by `solera-init` or on first `create`).

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas |
| **mode** | Y | `create` \| `update` \| `deprecate` \| `archive` | create |
| **journey_id** | Y | Kebab-case ID | first-time-checkout |
| **journey_name** | N | Human-readable name (defaults to title-cased id) | First-time Checkout |
| **walks** | Y (in `create`) | Persona id this Journey is walked by — exactly one | small-cafe-owner |
| **parent** | N | Parent Journey id; omit or `null` for a top-level Journey | onboarding |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create | Journey file | `{project_path}/.solera/journeys/{journey_id}.md` | Final |
| Wrap-up | Updated index | `{project_path}/.solera/journeys/_index.md` | Final |

## Procedure

### 1. Setup

- [ ] Confirm `{project_path}/.solera/personas/_index.md` exists and contains ≥1 active Persona. If not, stop and advise `solera-write-persona`.
- [ ] Ensure `{project_path}/.solera/journeys/` exists; create if missing.
- [ ] Ensure `{project_path}/.solera/journeys/_index.md` exists; if missing, scaffold from [assets/_index-template.md](assets/_index-template.md).
- [ ] Resolve journey file path: `{project_path}/.solera/journeys/{journey_id}.md`.
- [ ] Branch by `mode`:
  - `create` — file must **not** exist → proceed to Create.
  - `update` / `deprecate` / `archive` — file **must** exist → proceed.
  - Violation → stop with a clear error.

### 2. Create (mode = create)

- [ ] Read [assets/journey-template.md](assets/journey-template.md).

- [ ] **Resolve `walks`** (required, exactly one Persona):
  - If `walks` argument provided: validate the named Persona exists + is `active`. On failure, halt with the list of active Personas.
  - Otherwise: ask the human:
    > "Which Persona walks this Journey? (exactly one — multi-persona journeys must be split)"
  - If the human names a Persona that is not yet drawn: stop and advise `solera-write-persona` first.

- [ ] **Ask the human for the Trigger** (blocking):
  > "What kicks off this Journey for `{persona_id}`? One sentence — the moment they start."
  - Reject empty / placeholder responses.
  - AI **must not** invent the Trigger; only refine wording with approval.

- [ ] **Offer AI observations before drafting Steps** (advisory):
  - Scan `journeys/*.md` for Journeys walked by the same Persona — overlap suggests this is a variant (consider `parent`).
  - Scan `narratives/*.md` for `in_journey: {journey_id}` references not yet anchored.
  - Present findings as:
    ```
    Observations (for your consideration — not decisions):
    - Persona "{walks}" already walks: {other_journey_ids}.
    - Narratives that may belong here once this Journey exists: {narrative_ids}.
    ```
  - Ask: "Does any of this change how you'd like to draw this Journey?"

- [ ] **Ask the human for Steps** (blocking, table-driven):
  - Prompt: "Walk me through the steps. For each step: stage / what they do / touchpoint (screen, channel) / emotion (😀 😐 😟) / pain (if any)."
  - Accept rows one at a time OR a paste-in markdown table.
  - AI may suggest reordering or splitting a step **only as a question**, never silently edit.

- [ ] **Ask the human for the Outcome** (blocking):
  > "What does success look like at the end? One sentence — what the Persona has achieved or how they feel."
  - Reject placeholder responses.

- [ ] **Resolve `parent`** (AI proposes; human decides):
  - If invocation passed `parent`: validate exists + is `active`. On failure, halt.
  - Otherwise: infer a candidate from observed Journeys walked by the same Persona with overlapping Trigger/Steps. Examples:
    - This Journey is a narrower variant of an existing one (e.g., `first-time-checkout` under `checkout`).
  - Present the candidate as a proposal; human chooses accept / different / `null`.
  - **Reject cycles and self-parenting** per axes-and-status.md.

- [ ] Write the Journey file using the template, filling:
  - Frontmatter: `id`, `kind: journey`, `name`, `status: active`, `created: {today in YYYY-MM-DD}`, `walks: {persona_id}`.
  - `parent: {parent_id}` — include only if a parent was resolved; **omit the line entirely** for top-level Journeys.
  - All sections from human input.
  - Keep the `## Workflow` section from the template intact.

- [ ] Proceed to Wrap-up.

### 3. Update (mode = update)

- [ ] Read the existing Journey file.
- [ ] Ask the human what to change. Offer a small menu:
  - Trigger
  - Steps (the table)
  - Outcome
  - Related (Narratives / Concepts cross-links)
  - **walks** (re-home to a different Persona — rare; usually means the Journey is conceptually different and should be a new file)
  - **Parent** (re-home under different parent or promote to top-level)
- [ ] For each chosen section, show current content, ask for new content, replace after confirmation.
- [ ] **When `walks` is chosen**: warn the human — "Re-homing a Journey to a different Persona is rare. Consider whether this is actually a new Journey for the new Persona. Continue?" Validate the new Persona exists + is `active`.
- [ ] **When `parent` is chosen**: same validation as Concept (axes-and-status.md → `parent`).
- [ ] Append `<!-- updated: YYYY-MM-DD -->` at the top of each edited section.
- [ ] Proceed to Wrap-up.

### 4. Deprecate (mode = deprecate)

- [ ] Ask the human for a one-line reason.
- [ ] Set `status: deprecated`.
- [ ] Prepend `> ⚠️ Deprecated {date} — {reason}` below frontmatter.
- [ ] Keep all other content intact.
- [ ] Proceed to Wrap-up.

### 5. Archive (mode = archive)

- [ ] Ask the human to confirm. Note: Narratives anchored via `in_journey: {journey_id}` become loose.
- [ ] Set `status: archived`.
- [ ] Proceed to Wrap-up.

### 6. Wrap-up

- [ ] Update `{project_path}/.solera/journeys/_index.md`:
  - `active` section lists all `active` Journeys, **grouped by `walks` Persona**, then indented by `parent` chain within each Persona group.
  - `deprecated` section flat.
  - Archived files are **not** listed (file remains on disk).
  - Orphans (parent missing or non-`active`, or `walks` Persona deprecated/archived) render with `— ⚠️ orphan` marker.
- [ ] Emit a short summary to the user:
  - For `create`: "Journey `{id}` drawn (walked by `{walks}`{parent_note}). Index updated."
  - For `update`: "Journey `{id}` updated: {sections changed}."
  - For `deprecate`/`archive`: "Journey `{id}` now {status}."

## Human–AI Protocol

This skill belongs to the same Moment 1 family as `solera-write-concept` and `solera-write-persona`.

| AI does | AI does not |
|---------|-------------|
| Ask clarifying questions about each step | Invent the Trigger, Steps, or Outcome |
| Offer observations from sibling Journeys / Narratives | Merge / split Journeys unilaterally |
| Suggest reordering steps as a question | Silently rewrite the steps table |
| Propose a `parent` based on overlap | Write `parent` silently |
| Validate the `walks` Persona exists | Auto-pick a Persona when none is provided |

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| No active Personas | `personas/_index.md` empty | Advise `solera-write-persona` first | Halt |
| Unknown `walks` Persona | Named Persona missing or non-`active` | List active Personas; halt | Halt until fixed |
| Create conflict | File exists in `create` mode | Offer `update` or archive/create-new | Halt until mode resolved |
| Update target missing | File absent in `update`/`deprecate`/`archive` | Offer `create` mode | Halt until mode resolved |
| Unknown parent | `parent` references a non-existent Journey | List available; halt | Halt until fixed |
| Inactive parent | `parent` exists but non-`active` | Ask for different parent (or top-level) | Halt until fixed |
| Self-parent | `parent == journey_id` | Reject | Halt until fixed |
| Parent cycle | Setting parent would loop | Show chain; reject | Halt until fixed |
| Persona changed mid-Journey | Human asks to change `walks` | Warn; suggest creating a new Journey instead | Continue if human insists |

## Completion Checklist

- [ ] Journey file at expected path with all required sections
- [ ] Frontmatter `id`, `kind`, `name`, `status`, `created`, `walks` present and correct
- [ ] Trigger and Outcome provided by human (not AI-generated)
- [ ] Steps table populated with at least one row from human input
- [ ] `_index.md` reflects the file's current status
- [ ] Summary message delivered to user
