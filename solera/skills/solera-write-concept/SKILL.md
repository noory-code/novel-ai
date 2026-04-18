---
name: solera-write-concept
user-invocable: true
description: Draw, update, deprecate, or archive a Concept — the living abstract areas that make up the project map.
metadata:
  version: "1.1.0"
  category: writing
  type: unit
  style: procedural
  triggers: [write a concept, draw a concept, add a concept, update concept, deprecate concept, archive concept, concept map]
  uses: []
---

<!-- SSOT: ../../docs/reference/axes-and-status.md — Concept status values (`active`/`deprecated`/`archived`) and transitions live there -->

# Writing Concept

> A Concept is a living, unfinished region of the project map.
> Humans draw Concepts; AI proposes and questions, never decides alone.
> Concepts never end — they evolve as Stories contribute to them.

## Philosophy

Concepts belong to the **Living Axis** — the side of Solera that does not end.
A Concept holds:

- **Intent** — the north star; what this Concept means in this project (rarely changes).
- **Current Design** — what the human is drawing right now; the ideal. Evolves.
- **Current Shape** — the AI-summarized As-Built; what has actually been produced so far. Updated when Stories wrap up.
- **Health** — 🟢/🟡/🔴 signals.
- **Contributions** — append-only log of Stories that advanced this Concept.
- **Related Artifacts** — published design artifacts and external links.

A Concept may optionally declare a `parent` — another Concept it sits inside.
See [axes-and-status.md → `parent` (Concept → Concept)](../../docs/reference/axes-and-status.md#parent-concept--concept) for cycle/self-parent/archive rules.

This skill handles four modes:

| Mode | When |
|------|------|
| `create` | Drawing a brand-new Concept |
| `update` | Revising Current Design / Horizon / Health on an existing one |
| `deprecate` | Concept is losing relevance but still referenced in history |
| `archive` | Concept is fully retired and should drop from the active index |

## Prerequisites

- `{project_path}/workspace/identity/mission.md` should exist (human knows who they are before drawing the map).
  - If not: ask the user to invoke `solera-write-identity` first.
- `{project_path}/workspace/concepts/` directory (created by `solera-init` or on first `create`).

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas |
| **mode** | Y | `create` \| `update` \| `deprecate` \| `archive` | create |
| **concept_id** | Y | Kebab-case ID of the Concept | authentication |
| **concept_name** | N | Human-readable name (defaults to title-cased id) | Authentication |
| **parent** | N | Parent Concept id; omit or `null` for a top-level Concept | banas-app |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create | Concept file | `{project_path}/workspace/concepts/{concept_id}.md` | Final |
| Wrap-up | Updated index | `{project_path}/workspace/concepts/_index.md` | Final |

## Procedure

### 1. Setup

- [ ] Confirm `{project_path}/workspace/identity/mission.md` exists (Glob). If missing, stop and ask user to run `solera-write-identity`.
- [ ] Ensure `{project_path}/workspace/concepts/` exists; create if missing.
- [ ] Ensure `{project_path}/workspace/concepts/_index.md` exists; if missing, scaffold from [assets/_index-template.md](assets/_index-template.md).
- [ ] Resolve concept file path: `{project_path}/workspace/concepts/{concept_id}.md`.
- [ ] Branch by `mode`:
  - `create` — file must **not** exist → proceed to Create.
  - `update` / `deprecate` / `archive` — file **must** exist → proceed to Update.
  - Violation → stop with a clear error.

### 2. Create (mode = create)

- [ ] Read [assets/concept-template.md](assets/concept-template.md).

- [ ] **Ask the human for the Intent** (blocking). Prompt in the user's language:
  > "What does this Concept mean in this project? One or two sentences — a north star that should rarely change."
  - Reject empty, single-word, or obvious placeholder responses ("tbd", "later", ".", etc.). Ask again with a concrete example to prime.
  - If the human replies with "just write it" / "you decide" / equivalent: **do not proceed**. Respond:
    > "Intent is the one thing I can't write for you — it's the north star. But I can suggest 2–3 candidate directions based on what the project already contains, and you pick or reject. Shall I?"
    Produce candidates only from observed artifacts (identity, existing Concepts, Stories). Human must choose or reword one; otherwise loop.
  - AI **must not** invent the Intent; only refine wording after the human proposes.

- [ ] **Offer AI observations before writing Current Design** (advisory, non-blocking):
  - Scan `concepts/*.md` for already-active Concepts with overlapping names or artifacts.
  - Scan `catalog/published/persona/`, `service-map/`, `journey/`, `use-case/`, `domain-model/` for artifacts that might belong to this Concept.
  - Scan `stories/*/\_story.md` (if any) for earlier contributions that should be retro-linked.
  - Present findings as:
    ```
    Observations (for your consideration — not decisions):
    - Possibly overlaps with Concept "{other_id}" on {reason}.
    - Artifacts that may relate: persona/{x}, service-map/{y}.
    - Prior Stories referencing similar scope: STORY-NNN.
    ```
  - Ask the human: "Does any of this change how you'd like to draw this Concept?"

- [ ] **Ask the human for Current Design** (blocking):
  > "How are you drawing this Concept right now? What's the ideal shape in your head?"
  - AI may ask clarifying questions.
  - AI may **not** write the Current Design on behalf of the human.
  - AI may offer to reword the human's answer for clarity — **word-smithing only, no new ideas**. Present the reworded version side-by-side with the original and require explicit approval. If the human wants substantive additions, ask targeted questions instead of inserting content.

- [ ] **Resolve `parent`** (AI proposes; human decides):
  - If the invocation passed a `parent` argument: validate it exists + is `active`. On failure, halt with a clear error.
  - Otherwise: infer a candidate parent from the new Concept's Intent/Current Design + existing `concepts/_index.md`. Examples of signals:
    - Vocabulary overlap with an existing Concept's Intent (e.g., new "Profile Edit" ↔ existing `profile`).
    - Explicit reference by the human in conversation ("this goes under Me tab" → `me`).
    - Product surface implied by language ("어드민 전용" → `banas-admin` if it exists).
    Present the candidate as a proposal:
    > "이 Concept이 `{candidate_id}` 아래에 들어가는 게 자연스러워 보입니다. 맞나요? 아니면 다른 parent, 아니면 top-level로 두시겠어요?"
  - Human chooses: accept candidate / specify a different parent id / explicit `null` (top-level).
  - **Reject cycles and self-parenting** per [axes-and-status.md → `parent`](../../docs/reference/axes-and-status.md#parent-concept--concept). Walk the chain from the proposed parent upward; if we revisit `concept_id`, halt.
  - AI must **never** invent a parent silently. "No parent found" is fine; proposing `null` is fine.

- [ ] Write the Concept file using the template, filling:
  - Frontmatter: `id`, `name`, `status: active`, `created: {today in YYYY-MM-DD}`.
  - `parent: {parent_id}` — include only if a parent was resolved; **omit the line entirely** for top-level Concepts (don't write `parent: null`).
  - `# Intent` — from the human, word-for-word (or human-approved rewording).
  - `# Current Design` — from the human.
  - `# Current Shape` — initially: `(no Stories have contributed yet)`.
  - `# Horizon` — optional; ask: "Any direction you expect this to extend toward? (can skip)".
  - `# Health` — default all 🟢/🟡/🔴 rows empty; add a one-line note if the human volunteers.
  - `# Contributions` — empty table header only.
  - `# Related Artifacts` — insert links the human confirms from the Observations step.
  - Keep the `## Workflow` section from the template intact (it is the SSOT for this Concept's own Setup/Create/Wrap-up).

- [ ] Proceed to Wrap-up.

### 3. Update (mode = update)

- [ ] Read the existing Concept file.
- [ ] Ask the human what to change. Offer a small menu:
  - Current Design
  - Horizon
  - Health
  - Related Artifacts
  - **Parent** (re-home this Concept under a different parent or promote to top-level)
  - Something else (free text)
- [ ] For each chosen section, show the current content, ask for the new content, and replace after human confirmation.
- [ ] **Intent is not editable here.** If the human wants to change Intent:
  - Stop and ask: "Intent is meant to be the unchanging north star. Changing it means this is effectively a different Concept. Do you want to (a) archive this one and create a new Concept, or (b) confirm the Intent rewording is a clarification of the same idea?"
  - Proceed only after explicit human answer.
- [ ] **When `parent` is chosen for editing**:
  - Show the current parent (or "(top-level)").
  - Ask for a new parent id or `null` (top-level).
  - Validate per [axes-and-status.md → `parent`](../../docs/reference/axes-and-status.md#parent-concept--concept):
    - Target Concept exists and is `active` (reject otherwise).
    - Target is not `concept_id` itself (self-parent).
    - Setting target does not create a cycle (walk proposed_parent's ancestor chain; if we hit `concept_id`, reject).
  - On `null`: **remove** the `parent:` line from frontmatter rather than writing `parent: null`.
- [ ] Append a `<!-- updated: YYYY-MM-DD --> ` HTML comment at the top of the edited section for auditability.
- [ ] Proceed to Wrap-up.

### 4. Deprecate (mode = deprecate)

- [ ] Ask the human for a one-line reason: "Why is this Concept being deprecated?"
- [ ] Set `status: deprecated` in frontmatter.
- [ ] Prepend a `> ⚠️ Deprecated {date} — {reason}` block below the frontmatter.
- [ ] Keep all other content intact (history is preserved).
- [ ] Proceed to Wrap-up.

### 5. Archive (mode = archive)

- [ ] Ask the human to confirm: "Archive removes this Concept from the active index. The file stays on disk. Continue?"
- [ ] Set `status: archived` in frontmatter.
- [ ] Proceed to Wrap-up.

### 6. Wrap-up

- [ ] Update `{project_path}/workspace/concepts/_index.md`:
  - `active` section lists all files with `status: active`, linked, **indented by parent chain**:
    - Top-level Concepts (no `parent:`) at indent 0.
    - Each child at its parent's indent + 2 spaces.
    - Render recursively so arbitrary depth stays readable.
    - Preserve deterministic ordering (alphabetical by id within each sibling group).
  - `deprecated` section lists all files with `status: deprecated` (flat — hierarchy less meaningful once a Concept is leaving).
  - Archived files are **not** listed in the index (but remain on disk).
  - If a Concept's `parent:` references an id that no longer exists or is non-`active`, treat it as orphan and render at indent 0 with a trailing `— ⚠️ orphan` marker.
- [ ] Emit a short summary to the user:
  - For `create`: "Concept `{id}` drawn{parent_note}. Intent fixed. Current Design captured. Index updated."
    - `{parent_note}` = ` under {parent_id}` if parent set, else ` as a top-level Concept`.
  - For `update`: "Concept `{id}` updated: {list of sections changed}."
  - For `deprecate`/`archive`: "Concept `{id}` now {status}."

## Human–AI Protocol

This skill is a **Moment 1 skill** (Concept Drawing). The collaboration rule is:

| AI does | AI does not |
|---------|-------------|
| Ask clarifying questions | Invent Intent or Current Design |
| Offer observations from the codebase / artifacts | Merge / split Concepts unilaterally |
| Rephrase for clarity, with human approval | Mark anything as final without human confirmation |
| **Propose a `parent` based on observed overlap / context** | **Write `parent` silently without the human confirming** |
| Update the index and file structure | Decide that a Concept is deprecated or archived without the human asking |

If at any point the human asks the AI to "just write it", the AI should still surface a proposed draft and wait for confirmation before persisting — the file is the human's drawing.

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| Missing identity | `mission.md` absent | Ask user to run `solera-write-identity` | Skill halts |
| Create conflict | File exists in `create` mode | Offer `update` or archive/create-new | Skill halts until mode resolved |
| Update target missing | File absent in `update`/`deprecate`/`archive` | Offer `create` mode | Skill halts until mode resolved |
| Intent rewrite in update | Human wants to edit Intent | Branch decision dialog (archive-and-new vs clarify) | Skill halts until chosen |
| Unknown parent | `parent` references a non-existent Concept | List available Concepts; halt | Skill halts until fixed |
| Inactive parent | `parent` exists but is `deprecated`/`archived` | Ask for a different parent (or top-level) | Skill halts until fixed |
| Self-parent | `parent == concept_id` | Reject | Skill halts until fixed |
| Parent cycle | Setting parent would loop back through `concept_id` | Show the chain; reject | Skill halts until fixed |
| Index corruption | `_index.md` malformed | Rebuild from filesystem scan of `concepts/*.md` | Continues |

## Completion Checklist

- [ ] Concept file at expected path with all required sections
- [ ] Frontmatter `id`, `name`, `status`, `created` present and correct
- [ ] Intent provided by human (not AI-generated)
- [ ] `_index.md` reflects the file's current status
- [ ] Summary message delivered to user

## Examples

### Example: creating "Authentication"

Invocation:
```
Skill(name="solera-write-concept", args={
  "project_path": "banas",
  "mode": "create",
  "concept_id": "authentication",
  "concept_name": "Authentication"
})
```

After Create step, the file looks like:
```markdown
---
id: authentication
name: Authentication
status: active
created: 2026-04-15
---

# Intent
사용자가 자신의 정체를 증명하고 적절한 권한을 받는 방법.

# Current Design
이메일/패스워드 + 구글 OAuth 를 1차 경로로 삼는다. 2FA 는 옵션. 관리자 권한은 별도 경로.

# Current Shape
(no Stories have contributed yet)

# Horizon
Passkey 전환을 장기적으로 검토. 엔터프라이즈 SSO 는 수요 관찰.

# Health
- 🟢
- 🟡
- 🔴

# Contributions
| Story | 무엇을 남겼나 | 날짜 |
|-------|---------------|------|

# Related Artifacts
- Personas: [[persona/primary-user]]
- Service Map: [[service-map/auth-flow]]

## Workflow
(see template)
```

And `_index.md` gains:
```markdown
- [Authentication](authentication.md) — 사용자가 자신의 정체를 증명하고 적절한 권한을 받는 방법.
```
