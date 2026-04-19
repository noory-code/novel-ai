---
name: solera-write-milestone
user-invocable: true
description: Reach a human–AI agreement on scope — which Concepts advance to what depth before the next release. The Moment 2 skill.
metadata:
  version: "1.0.1"
  category: writing
  type: unit
  style: procedural
  triggers: [write a milestone, agree on milestone, define milestone scope, plan next release scope, milestone agreement]
  uses: []
---

<!-- SSOT: ../../docs/reference/axes-and-status.md — Milestone status values (`proposed`/`agreed`/`in-progress`/`released`) and transitions live there -->

# Writing Milestone

> A Milestone is a **human–AI agreement** on scope, not a deadline.
> "These Concepts, to these depths, before we call it done."
> The Moment 2 skill: the conversation that must happen before work starts.

## Philosophy

This skill exists because Solera's core flow is **계획 → 일 → 결과 확정**, and the 계획 step must not be a human monologue. The human proposes scope; the AI reads the current state of every Concept and **must push back** — maturity, risks, dependencies, missing prerequisites — before the scope is frozen.

Without this skill, Stories start running toward targets the human set alone, and drift is discovered only in retrospect.

### The Agreement Cycle (Create step)

```
Human proposes       AI analyzes          Human revises
──────────────────► ────────────────────► ────────────────┐
                                                           │
                                                           ▼
                                   Repeat until stable  ──► agreed
```

AI must produce at least **one analysis round per iteration** — never silently accept the human's first proposal. If the AI has no concerns, it must say so explicitly ("I see no issues with this scope because X, Y, Z") rather than skipping the round.

## Prerequisites

- `{project_path}/.solera/concepts/_index.md` exists with at least one active Concept.
  - If not: stop and ask the user to run `solera-write-concept` first.
- `{project_path}/.solera/identity/mission.md` exists.
- `{project_path}/.solera/milestones/` directory (created by `solera-init` or on first invocation).

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas |
| **mode** | Y | `create` \| `update` \| `mark-released` | create |
| **milestone_id** | Y | Kebab-case ID | mvp, v0-2-alpha |
| **milestone_name** | N | Human-readable name (defaults to title-cased id) | MVP Launch |
| **target_date** | N | ISO date; advisory only, not a gate | 2026-06-30 |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create | Milestone file | `{project_path}/.solera/milestones/{milestone_id}.md` | Final |
| Wrap-up | Updated index | `{project_path}/.solera/milestones/_index.md` | Final |

## Procedure

### 1. Setup

- [ ] Confirm `{project_path}/.solera/concepts/_index.md` exists and contains ≥1 active Concept. If not, stop and advise `solera-write-concept`.
- [ ] Ensure `{project_path}/.solera/milestones/` exists; create if missing.
- [ ] Ensure `{project_path}/.solera/milestones/_index.md` exists; if missing, scaffold from [assets/_index-template.md](assets/_index-template.md).
- [ ] Read `{project_path}/.solera/team-process.md` if it exists; extract `workflow_gates.milestone.agree` for use at the agreement boundary in Step 2.3.
- [ ] Branch by `mode`:
  - `create` — file must **not** exist → proceed to Create.
  - `update` — file must exist with `status ∈ {proposed, agreed, in-progress}` → proceed to Update.
  - `mark-released` — file must exist → proceed to Release Marking.

### 2. Create (mode = create) — The Agreement Cycle

This is the core of the skill. Execute **at least one full analysis round**, and loop until the human explicitly agrees.

#### 2.1 Ask for the scope proposal (blocking)

Prompt in the user's language:
> "이번 Milestone에 포함시키고 싶은 Concept들을 알려주세요. 각 Concept이 어느 깊이까지 가야 '이번엔 됐다' 인지도 간단히요."

- Accept answers like: "Authentication은 소셜 로그인까지. Search는 텍스트 검색만." or "MVP에는 A, B, C 모두."
- If the human names a Concept not present in `concepts/_index.md`: stop and ask whether they want to (a) draft that Concept first via `solera-write-concept`, or (b) drop it from scope.

#### 2.2 AI analysis round (required, non-negotiable)

AI must read the **current state** of every proposed Concept and produce a structured analysis. At minimum, every section below must be addressed — if there is nothing to report, write "(no concerns)" explicitly.

For each proposed Concept, AI reads:
- `concepts/{id}.md` — Intent, Current Design, Current Shape, Horizon, Health
- Any linked artifacts under `catalog/published/` that exist
- Stories in `stories/*/\_story.md` whose `contributes_to` includes this Concept (for recent momentum)

Then AI writes an analysis block to the user:

```
Analysis for {milestone_id}:

For each proposed Concept:
  {concept}:
    maturity: {how close Current Shape is to the proposed depth — "far / partial / close"}
    design_gaps: {what Current Design is silent about but the proposed depth requires}
    artifact_readiness: {missing prerequisites — e.g., "no journey exists yet"}
    health_flags: {any 🟡/🔴 items that could derail this scope}

Cross-concept concerns:
  dependencies: {Concept X assumes Concept Y reach certain depth first}
  contradictions: {Concept A's Current Design and Concept B's Current Design conflict on X}

Scope sanity:
  too_ambitious: {which items likely don't fit}
  missing: {Concepts not proposed that the human may have overlooked}
  stretch: {items that fit only if other things are cut}

If there is nothing to report in a section, say "(no concerns)" — do not omit the section.
```

#### 2.3 Human response (blocking)

Present the analysis and ask:
> "이 분석 중 조정하고 싶은 게 있으세요? 스코프를 바꾸거나, 제가 지적한 걸 무시하거나, 다음 라운드로 가시거나."

Possible human replies:
- **Revise scope** — return to 2.1 with new scope, run 2.2 again.
- **Accept with notes** — human acknowledges concerns but keeps scope as-is (AI records this as "accepted despite: …").
- **Agreed** — scope is final → run `milestone.agree` gate (below), then proceed to 2.4.

Loop 2.1–2.3 at least once after each revision. **Never mark as agreed on the first round without the human's explicit "agreed" / "합의" / equivalent.**

**Gate `milestone.agree` check** (if defined in team-process.md): iterate `checks[]` per **Gate check execution** below; halt on any failure. This is the last chance to block an agreement that would violate a team policy (e.g., "every scope Concept must already have a persona artifact").

#### 2.4 Write the milestone file

- [ ] Read [assets/milestone-template.md](assets/milestone-template.md).
- [ ] Fill:
  - Frontmatter: `id`, `name`, `status: agreed`, `target_date` (optional), `created: today`.
  - `# Scope` — each included Concept with depth note (verbatim from human's latest statement).
  - `# AI Analysis` — the **last round** of analysis (concise, not the entire back-and-forth).
  - `# Agreement Log` — one-line summaries of each round: "Round 1: human proposed X, AI flagged Y, human revised to Z." Minimum: one round.
  - `# Exit Criteria` — human-agreed condition for each scope item (e.g., "Authentication: Current Shape reflects 소셜 로그인 3개 동작하는 상태"). If not provided, prompt for it.
  - Keep `## Workflow` section from template intact.

- [ ] Proceed to Wrap-up.

### 3. Update (mode = update)

Used when scope needs to change mid-flight (e.g., a Story discovered a blocker).

- [ ] Read existing milestone file.
- [ ] Ask the human what to change:
  - Scope (add/remove Concept, change depth)
  - Exit Criteria
  - Target date
- [ ] For scope or exit-criteria changes: **run one analysis round** (steps 2.2–2.3). Target-date-only changes skip analysis.
- [ ] Append the new round to `# Agreement Log` with `<!-- updated: YYYY-MM-DD -->`.
- [ ] If the scope grew meaningfully, require the human to confirm they are not effectively starting a new milestone instead.

### 4. Release Marking (mode = mark-released)

- [ ] Read existing milestone file.
- [ ] Validate each `# Exit Criteria` entry — AI reports current Concept state vs criterion.
- [ ] If any criteria unmet: stop and list the gaps; **do not** set status.
- [ ] If all met: set `status: released`, set `released_at: today`.
- [ ] Advise the user that `solera-release` can now be invoked to freeze the snapshot.

### 5. Wrap-up

- [ ] Rebuild `_index.md`:
  - `proposed` — milestones with status=proposed
  - `agreed` / `in-progress` — active agreed milestones
  - `released` — released milestones (most recent first)
- [ ] Emit summary to user:
  - For `create`: "Milestone `{id}` agreed. {N} Concepts in scope. {M} analysis rounds recorded."
  - For `update`: "Milestone `{id}` updated: {list of changes}. Analysis round {K} recorded."
  - For `mark-released`: "Milestone `{id}` released. Ready for solera-release."

## Gate check execution

All `workflow_gates.*.checks[]` entries in `team-process.md` share the same execution model. For each check object, dispatch by `type`:

| `type` | What it does | `params` |
|---|---|---|
| `glob_exists` | Run `Glob {pattern}` — PASS if ≥1 match | `{ pattern: "path/glob" }` |
| `act_complete` | Read an `_story.md` Action Items table — PASS if every listed ACT ID has status ✅ | `{ ids: [ACT-001, ACT-002] }` |
| `command_passes` | Run command via Bash — PASS if exit code = 0 | `{ run: "npm test" }` |
| `grep_absent` | Run `Grep {pattern}` restricted to `{glob}` — PASS if 0 matches | `{ pattern: "TODO\|FIXME", glob: "src/**/*.ts" }` |
| `concept_exists` | For each `concept_id` in params (or this milestone's scope Concept IDs if params empty), Glob `concepts/{id}.md`; PASS if all exist with `status: active` | `{ ids: [authentication] }` or `{}` (defaults to this milestone's scope) |
| `milestone_status` | Read `milestones/{id}.md`; PASS if its `status` matches `equals` | `{ id: "mvp", equals: "agreed" }` |

Rules:
- A gate with `checks: []` or no `checks` key falls back to text evaluation of the `condition` field.
- ALL checks must pass for a gate to pass. Any failure → halt with the failing check's `type` and `params` in the error message.
- Unknown `type` values → halt with `"unknown gate check type: {type}"` (do not silently skip).

## Human–AI Protocol

This skill is a **Moment 2 skill** (Milestone Agreement). The collaboration rule is strict:

| AI does | AI does not |
|---------|-------------|
| Read every proposed Concept's current state before analyzing | Skip the analysis round to save time |
| Flag maturity / dependency / missing prerequisite risks | Unilaterally reduce scope |
| Offer missing Concepts the human may have overlooked | Add Concepts to scope without human approval |
| Report "no concerns" explicitly when analysis truly finds nothing | Quietly omit the analysis section |
| Record disagreements in Agreement Log when human overrides | Erase or soften recorded concerns |

**If the human says "그냥 합의하자" / "skip analysis" / equivalent**: the AI must still produce an analysis — even a one-liner ("All Concepts are at the proposed depth already; no concerns.") — and log it. The analysis round is non-negotiable because it is Solera's structural guarantee that scope was examined.

## Error Handling

| Failure point | Condition | Recovery | Exit behavior |
|---|---|---|---|
| No active Concepts | `_index.md` has none | Ask user to run `solera-write-concept` | Skill halts |
| Proposed Concept not found | Named ID has no file | Offer (a) draft that Concept first, (b) drop from scope | Skill pauses until chosen |
| Analysis refusal | Human wants to skip | Produce minimal one-line analysis anyway, log it | Continue |
| Mark-released with unmet criteria | Some criteria still open | List gaps; do not change status | Skill halts |
| File conflict on create | File exists | Offer update mode | Skill halts until resolved |

## Completion Checklist

- [ ] Milestone file at expected path with all required sections
- [ ] Frontmatter `id`, `name`, `status`, `created` present
- [ ] `# Scope` lists Concepts with depth notes
- [ ] `# AI Analysis` present (every section, even if "(no concerns)")
- [ ] `# Agreement Log` has ≥ 1 round
- [ ] `# Exit Criteria` defined for each scope item
- [ ] `_index.md` reflects the file's current status
- [ ] Summary delivered to user

## Examples

### Example: creating "mvp" milestone for banas

Invocation:
```
Skill(name="solera-write-milestone", args={
  "project_path": "banas",
  "mode": "create",
  "milestone_id": "mvp",
  "milestone_name": "MVP Launch",
  "target_date": "2026-06-30"
})
```

Round 1:
- Human: "Authentication 소셜 로그인까지, Onboarding 역할 선택까지, Liquor-search 텍스트 검색만."
- AI analysis surfaces: "Onboarding의 Current Shape이 비어있음. Current Design에 역할 선택 플로우는 있으나 실제 구현 전. Authentication 완료 후 시작 의존성 있음. Liquor-search는 Journey 아티팩트 없음 — 먼저 그리는 것 권장."
- Human: "Journey는 Story 안에서 같이 만드는 걸로. 의존성은 알고 있음."

Round 2:
- AI: "(no new concerns). 기록된 받아들인 위험: Liquor-search의 Journey 부재."
- Human: "합의."

File written, `_index.md` updated, summary delivered.
