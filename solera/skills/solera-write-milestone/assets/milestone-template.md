---
id: {milestone_id}
name: {milestone_name}
status: agreed
target_date: {YYYY-MM-DD or omitted}
created: {YYYY-MM-DD}
---

# Scope

<!-- Each included Concept with depth note — verbatim from the human's latest statement.
     Example:
     - Authentication: 소셜 로그인(Google, Apple, Kakao) 완료까지
     - Onboarding: 역할 선택 + 첫 탐색 진입까지
     - Liquor-search: 텍스트 검색만 (음성/이미지 제외)
-->

# AI Analysis

<!-- The last analysis round. Every section must be present. Use "(no concerns)" when empty. -->

For each proposed Concept:
  {concept}:
    maturity: (…)
    design_gaps: (…)
    artifact_readiness: (…)
    health_flags: (…)

Cross-concept concerns:
  dependencies: (…)
  contradictions: (…)

Scope sanity:
  too_ambitious: (…)
  missing: (…)
  stretch: (…)

# Agreement Log

<!-- One line per round. Minimum one entry.
     Format: "Round N (YYYY-MM-DD): {what happened — human proposal, AI flags, human decision}"
-->

- Round 1 ({date}): human proposed {X}; AI flagged {Y}; human revised to {Z}.

# Exit Criteria

<!-- Per scope item, the human-agreed condition that signals "done enough".
     Expressed as a statement about the Concept's Current Shape.
     Example:
     - Authentication: Current Shape reflects 3 social providers wired end-to-end with role assignment on first login.
     - Onboarding: Current Shape reflects 역할 선택 UI + 첫 탐색 화면 진입 동작.
-->

# Accepted Risks

<!-- Optional. Record concerns the AI raised that the human chose to accept anyway.
     Format: "- {concern} — accepted because {reason}." -->

(none)

## Workflow

### Step 0. Setup
- [ ] Ensure `concepts/_index.md` has ≥1 active Concept
- [ ] Ensure `milestones/` and `_index.md` exist
- [ ] Enforce mode (create → file absent, update/mark-released → file present)

### Step 1. Create (mode = create) — Agreement Cycle
- [ ] Human proposes scope (blocking)
- [ ] AI runs one analysis round over all proposed Concepts (non-negotiable)
- [ ] Human responds: revise / accept with notes / agreed
- [ ] Loop until human explicitly agrees
- [ ] Write file: Scope, AI Analysis (last round), Agreement Log (all rounds), Exit Criteria
- [ ] `status: agreed`

### Step 2. Update (mode = update)
- [ ] Human picks what to change (scope, exit criteria, target date)
- [ ] Scope or exit-criteria changes → one analysis round required
- [ ] Append new round to Agreement Log with `<!-- updated: YYYY-MM-DD -->`

### Step 3. Mark Released (mode = mark-released)
- [ ] AI verifies each Exit Criterion against current Concept state
- [ ] If all met → `status: released`, `released_at: today`
- [ ] If any unmet → halt, list gaps

### Step 4. Wrap-up (all modes)
- [ ] Rebuild `_index.md` (proposed / agreed / released sections)
- [ ] Emit summary to user
