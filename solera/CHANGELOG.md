# Changelog

## [3.0.3] — 2026-04-17

### Fixed

- **`solera-migrate-v2` banned phrase leak**: Step 1 Procedure contained `"if needed"` — one of the five AI-First banned phrases its own self-verification rule (C-001) forbids. The ambiguous instruction is replaced with an explicit condition (`when the parent does not exist`).
- **Test suite validated v2 schema**: `tests/test_skill_validation.py` still required `phase_id`, `goal_id`, `epic_name`, and `_epic.md` prerequisites — parameters that v3.0.0 removed. The suite passed regardless of whether `solera-write-story` or `solera-execute-action-item` followed v3. Tests now pin the v3 contract (`story_id`, `contributes_to`, Concept-based prerequisites, `[primary_concept][story_id][ACT-NNN]` commit format) and actively guard against v2 regression by asserting forbidden parameters are absent.

### Changed

- **Three-axis and status SSOT centralised** in the new canonical reference `docs/reference/axes-and-status.md`. Four files that previously defined (or redefined) axis tables and status values now link to it: `docs/work-item-structure.md`, `skills/solera-manage-workflow/assets/conventions.md`, `skills/solera-init/assets/solera-workflow.md`, and the five core writing-skill SKILL.md files which gained a `<!-- SSOT: docs/reference/axes-and-status.md -->` marker. Renaming an axis or adding a status value is now a one-file edit.
- **Self-verification schema centralised** in `docs/reference/self-verification-schema.md`. The `## Structural` / `## Semantic` format with `id:`-addressable rules is declared canonical; `C-001` is reserved across all skills for the AI-First banned phrases check with `"handle accordingly"` added to the canonical pattern list. Every `skills/*/assets/self-verification.md` was aligned:
  - `solera-handoff/assets/self-verification.md` converted from the legacy TC### format to the canonical schema.
  - `solera-execute-action-item`, `solera-write-story`, and `solera-create-pr` gained the canonical `C-001` rule; their prior `C-001` content was renumbered to `C-040` to preserve meaning.
  - The six skills that already had `C-001` now include `"handle accordingly"`, matching the canonical list.
- **`solera-migrate-v2`** v1.2.0 → v1.3.0.
  - Resume Semantics now derives the last completed step **deterministically** from `Solera-Migrate-Step: N-name` commit trailers; filesystem signals are the fallback. Each of the seven step commits adds the trailer.
  - `"if needed"` (Step 1) replaced with an explicit precondition.
- **`retro.md` → `retrospective.md`** asset file rename across three skills (`solera-write-story`, `solera-manage-workflow`, `solera-execute-action-item`). Filename now matches the document it targets (`RETROSPECTIVE.md`). All cross-references updated.

### Notes

- This release is entirely maintenance — no user-facing behaviour changes. Existing workspaces do not need any action.
- The canonical references under `docs/reference/` are the single source of truth for axes, status values, and self-verification schema. Future edits to those concepts start there.

---

## [3.0.2] — 2026-04-16

### Fixed

- **`solera-migrate-v2` Step 1 archive policy**: previous versions used a name-based rule ("skip directories whose name matches a v3 name") to decide what to archive. This misfired on v2 projects where `workspace/identity/`, `workspace/catalog/`, or `workspace/team-process.md` already existed but contained v2 data — those paths would be skipped and v2 content would pollute the v3 skeleton. Step 1 now moves the **entire** `workspace/` contents into `_v2-archive/workspace-original/` regardless of name, and Step 2 copies selectively from the archive. Safer and unambiguous.
- **`solera-migrate-v2` concept → domain-model rename scope**: v1.1.0 only renamed `_v2-archive/catalog/published/concept/`, missing `_v2-archive/extra/*/concept/` and `_v2-archive/extra/*/published/concept/` (nested Obsidian vault layouts). Step 2.3 now enumerates all three source locations for the rename.
- **`solera-migrate-v2` loose files at vault roots**: v2 Obsidian vaults often contain `.md` files directly at the vault root (e.g., `README.md`, `app-structure.md`) that don't live inside a `{type}/` subdirectory. Previously these were silently left in `_v2-archive/` and lost during migration. Step 2.3 now scans for loose files at both the archived workspace root and every extra vault root, and runs a BLOCKING prompt per file (route to `_unclassified/misc/`, provide target, or skip).

### Changed

- **`solera-migrate-v2`** v1.1.0 → v1.2.0.
  - Step 1 "Freeze" now archives every direct child of `{workspace_path}/` into `_v2-archive/workspace-original/` — no name-based exceptions.
  - Step 2 all source paths updated from `_v2-archive/{child}/` to `_v2-archive/workspace-original/{child}/`.
  - Step 2.3 "Catalog merge" covers three source locations for the concept→domain-model rename and three source locations for type enumeration (workspace catalog, extra root, extra/published nested layout).
  - Step 2.3 adds the "Loose files at vault roots" subroutine with BLOCKING prompt.
  - Origin comments injected into migrated Stories (Step 4) now reference the `workspace-original/` path.

### Migration Notes

- Projects migrated with v3.0.0 or v3.0.1 and no surprises are unaffected — v3.0.2 only changes the migration skill.
- Projects that hit the name-conflict, missing-concept-rename, or lost-loose-file issues during a v3.0.0/v3.0.1 migration can re-run `solera-migrate-v2` after upgrading; Resume Semantics detects Step 2 completion via `catalog/published/` state and lets you replay from the correct step.

---

## [3.0.1] — 2026-04-16

### Fixed

- **`solera-migrate-v2` identity source discovery**: v2 Obsidian-style vaults sometimes keep identity files outside `workspace/identity/` (e.g., in a separate vault root like `{project_path}/published/identity/`). Step 2 now collects candidate identity files from both `_v2-archive/identity/` and `_v2-archive/extra/*/identity/`, classifies standard vs non-standard, and asks the human about non-standard files instead of silently keeping or dropping them. Issues a warning if no standard identity files are found in any source.
- **Catalog merge for unknown artifact types**: v2 projects may contain artifact folders not in the v3 mapping (e.g., `schema/`, `reference/`, custom folders). Step 2.3 now runs a BLOCKING one-shot prompt per unknown type, letting the human route it to `catalog/published/_unclassified/{type}/`, map it to an existing v3 type, or skip. Previously unknown types relied on ad-hoc judgment at execution time.
- **Journey detection**: If an archived identity dir contains a `journeys/` subdir, Step 2.1 now moves its contents to `catalog/published/journey/` instead of treating them as identity.

### Changed

- **`solera-publish-artifacts`** v5.0.0 → v5.1.0.
  - Move Mapping table adds `reference/ → catalog/published/reference/`.
  - New **fallback row**: unknown types go to `catalog/published/_unclassified/{type}/` (previously "left in place + logged"). Step 1 Discovery now asks a BLOCKING one-shot prompt per unknown type before routing to fallback.
  - Error Handling row for "Unknown artifact type" updated to describe the BLOCKING fallback flow.

- **`solera-migrate-v2`** v1.0.0 → v1.1.0.
  - Step 2 expanded into three subsections (2.1 Identity copy policy, 2.2 team-process.md, 2.3 Catalog merge) with explicit policies for identity classification and unknown catalog types.
  - Resume Semantics table adds a signal row for Step 2 completion (`catalog/published/` populated).

### Documentation

- `docs/migrate-v2-to-v3.md` "What happens to your v2 data" table expanded to describe the new non-standard identity and unknown catalog type flows.

### Migration Notes

- Projects migrated with v3.0.0 are unaffected — v3.0.1 only changes behavior of the migration skill itself, not the resulting v3 workspace layout.
- If you ran the v3.0.0 migration and ended up with missing identity files or dropped artifact folders, re-run `solera-migrate-v2` after v3.0.1 to resume from Step 2; the skill's Resume Semantics will skip already-completed steps.

---

## [3.0.0] — 2026-04-16

### ⚠️ BREAKING CHANGES

v3 is a full architectural rework. The v2 single-hierarchy model (Identity → Initiative → Phase → Goal → Epic → Story → Action Item) is replaced with a three-axis model:

- **Living** — Identity, Concepts (never end; evolve continuously)
- **Time-bound** — Milestones, Stories, Action Items (have a start and end)
- **Immutable** — Releases (frozen snapshots, write-once)

**v2 projects cannot be opened directly by v3.** Use `solera-migrate-v2` to migrate.

### Removed

- `solera-write-phase` — Phase layer eliminated
- `solera-write-goal` — Goal layer eliminated
- `solera-write-epic` — Epic layer eliminated
- `workspace/initiative/` and `workspace/phase/` directory conventions
- Epic branches (`epics/{name}`) and Story-under-Epic branches (`epics-{name}/story-{id}-{name}`)
- `[epic-name][US-NNN][ACT-NNN]` commit scope tag
- Artifact promotion at Goal Create + Epic Wrap-up (two hooks collapsed into one)

### Added

- **`solera-write-concept`** v1.0.0 — draw / update / deprecate / archive Concepts with human-led Intent and Current Design; AI proposes Current Shape updates at Story Wrap-up. Modes: `create` / `update` / `deprecate` / `archive`. BLOCKING on Intent entry — AI must never invent it.
- **`solera-write-milestone`** v1.0.0 — the Moment 2 skill. Human proposes scope; AI runs a mandatory analysis round (maturity, risks, dependencies, missing prerequisites, cross-concept contradictions); loop until agreed. Modes: `create` / `update` / `mark-released`. Analysis round is **non-negotiable** — even "skip analysis" requests produce at least a one-liner.
- **`solera-release`** v1.0.0 — Moment 4 skill. Freezes an achieved Milestone into `releases/{tag}/` with a `concepts-snapshot/` (verbatim Concept copies with ❄️ markers), a `stories-manifest.md`, and a human-approved `README.md`. Refuses to overwrite an existing release directory. Optional `git tag` creation.
- **`solera-migrate-v2`** v1.0.0 — 7-step assisted migration skill. Non-destructive freeze of v2 data to `_v2-archive/`, v3 skeleton creation, AI-proposed Concept candidates from v2 Goals/Epics (human approval required), Story flattening with `contributes_to` inference (sample-reviewed), `releases/v2-final/` as the first immutable snapshot.
- **Three-axis `progress.md` format** — Living / Time-bound / Immutable sections instead of Phase/Goal/Epic/Story/ACT pointers.
- **Concept Contribution Summary** — required section in every Story `RETROSPECTIVE.md`, with Drift note capability.
- **Input Artifacts / Output Artifacts** — two distinct sections on every Story. Input provided by human at Step 2; Output appended by `solera-execute-action-item` during Execute.
- **Gate `concept.align`** — checks `contributes_to` is present, each Concept exists and is `active`.
- **Gate `milestone.agree`** — fires at Milestone agreement boundary.
- **Check type `concept_exists`** — for each concept_id (or `contributes_to` if empty), Glob `concepts/{id}.md`; PASS if all exist with `status: active`.
- **Check type `milestone_status`** — read `milestones/{id}.md`; PASS if `status` matches `equals`.
- **Gate check execution** — dispatch table inlined into each gate-running skill (`solera-write-story`, `solera-execute-action-item`, `solera-write-milestone`) for the 6 check types.

### Changed

- **`solera-write-story`** v9.0.1 → v10.0.0. Parameters simplified: removed `year`, `phase_id`, `goal_id`, `goal_name`, `epic_name`, `epic_type`; added `contributes_to` (required ≥1) and `belongs_to` (optional). Path flattened from `phase/.../epics/.../stories/{id}` to `stories/{id}-{name}/`. Branch: `story/{id}-{name}` from trunk. Commit scope tag uses `contributes_to[0]` (the primary_concept). New Step 5 subroutine at Wrap-up: AI proposes Current Shape update for each contributed Concept; BLOCKING on human approval; Contributions row appended.
- **`solera-execute-action-item`** v7.2.0 → v8.0.0. Parameters simplified: removed `year`, `phase_id`, `goal_id`, `goal_name`, `epic_name`, `epic_type`. Commit scope tag reads `_story.md` frontmatter `contributes_to[0]`. New Wrap-up obligation: append each completed ACT to the parent Story's `# Output Artifacts` section (required for Story Wrap-up's Current Shape draft). System improvements (`skill_change` / `rule_change`) now commit as a separate follow-up commit (`chore(solera): apply improvements from …`) instead of amending the ACT commit — preserves Atomic Commits.
- **`solera-manage-workflow`** v5.1.0 → v6.0.0. `uses` list updated to v3 skills. New 8-branch `next` action surfaces options based on three-axis state (ACT in progress → Story has ACTs → Story Wrap-up pending → Milestone Stories pending → Milestone Exit Criteria met → no Milestone but Concepts → no Concepts → no Identity). Supervisor explicitly state-aware but not opinionated; auto-picks only when one path is obvious (resume).
- **`solera-init`** v2.1.0 → v3.0.0. Detects v2 projects (`workspace/initiative/`, `workspace/phase/`, `_goal.md`, `_epic.md`) and refuses to overlay v3 — advises `solera-migrate-v2` instead. Creates v3 skeleton: `identity/`, `concepts/`, `milestones/`, `stories/`, `releases/`, `catalog/published/` + three `_index.md` seeds. Kickoff interview C-4 gate mapping updated to v3 gate keys.
- **`solera-publish-artifacts`** v4.0.0 → v5.0.0. Rewritten as a **Story Wrap-up hook** (v2 had two hooks: Goal Create + Epic Wrap-up — collapsed to one). Discovery source is `stories/{story_id}/artifacts/`. Version tag is `{story_id}`. New responsibility: wire the promoted files into each contributed Concept's `# Related Artifacts` section. Collision handling is now BLOCKING with three explicit options (Overwrite / Rename new / Skip) — no automatic rename.
- **Artifact rename: `concept` → `domain-model`**. The v2 Epic-level "concept" artifact (domain entity modeling) is renamed to `domain-model` so the word "Concept" can be used for the living axis. `catalog/published/concept/` → `catalog/published/domain-model/`. The v2 template is archived at `docs/reference/domain-model-template.md`.
- **`solera-help`** v1.0.0 → v3.0.0 — full rewrite with v3 skill table grouped by axis.
- **`solera-write-identity`** — minor update: the handoff suggestion at the end of Identity creation now points to `solera-write-concept` instead of `solera-write-phase`/`solera-write-goal`.

### Documentation

- `docs/work-item-structure.md` — rewritten around the three axes and four moments.
- `docs/architecture.md` — rewritten. New sections: Three-Axis Wiring, Why no supervisor state machine.
- `docs/quick-start.md` — rewritten end-to-end for v3 (Identity → Concept → Milestone → Story → Release).
- `docs/team-workflow.md` — rewritten. Stories are now the sole branching unit; Concept-level coordination and drift-detection mechanics explained.
- `docs/migrate-v2-to-v3.md` — new. Migration guide for `solera-migrate-v2`.
- `docs/reference/domain-model-template.md` — new. v2 concept template archived for reference.
- `README.md` — rewritten. Three-axis diagram, four-moments summary, v2 migration pointer.

### Migration Notes

- **v2 projects**: run `solera-migrate-v2` from a clean git state. Every step blocks for your approval; automatic destruction is impossible. Reversible via `git reset` if mid-flight.
- **No automatic v2 → v3 fallback**: `solera-init` refuses to touch existing v2 data.
- **v2 maintenance**: stay on v2.14.0 if you need to maintain a v2 project without migrating. v3 will not add features backported to v2.

---

## [2.14.0] — 2026-04-09

### Added
- **Action Item level gates**: `workflow_gates` now supports `act.start` and `act.done`
  gate keys for per-commit dependency management and automated verification
- `solera-execute-action-item` v7.2.0: Setup step checks `act.start` gate before
  execution; Wrap-up step checks `act.done` gate after commit (same structured
  `checks[]` mechanism as Story-level gates)
- `solera-init` v2.1.0: kickoff interview and team-process template include
  `act.start` / `act.done` gate configuration

---

## [2.13.0] — 2026-04-06

### Fixed
- **Handoff no longer forced**: `solera-handoff` triggers narrowed to explicit requests
  only (`handoff`, `save handoff`, `run handoff`, `update HANDOFF`). Removed broad
  triggers like `end session`, `save work context`, `hand over to next session`
- **solera-workflow.md**: handoff routing changed from "End session, wrap up" to
  explicit-only invocation
- **Anti-pattern guard**: `solera-workflow.md` and `solera-manage-workflow` now
  explicitly prohibit suggesting handoff after task completion — handoff is
  user-initiated only

### Changed
- `solera-handoff` v2.0.0 → v2.1.0
- `solera-manage-workflow` v5.0.1 → v5.1.0

---

## [2.12.0] — 2026-03-30

### Added
- **System improvement step**: `solera-execute-action-item` Wrap-up now classifies
  retrospective improvements into `skill_change`, `rule_change`, or `framework_change`
  and applies skill/rule changes immediately within the same commit

### Changed
- **Rename RETRO.md → RETROSPECTIVE.md** across all skills, templates, docs, and tests
  — eliminates ambiguity with "retro" (retrospective vs. vintage)
- Affected skills patched: `solera-write-story` v9.0.1, `solera-write-epic` v5.0.1,
  `solera-write-goal` v5.0.1, `solera-write-phase` v3.0.1, `solera-manage-workflow` v5.0.1,
  `solera-execute-action-item` v7.1.0

---

## [2.11.0] — 2026-03-30

### Added
- **execution_order enforcement**: `solera-write-story` Step 3 validates ACT phase
  assignments against `execution_order.groups` from team-process.md — ensures
  layered architecture ordering (e.g., Domain before Data before Presentation)
- **Structured gate verification**: `workflow_gates` in team-process.md now supports
  a `checks[]` array with deterministic check types (`glob_exists`, `act_complete`,
  `command_passes`, `grep_absent`). `solera-write-story` Steps 4-5 iterate checks
  programmatically. Falls back to text-based evaluation when `checks` is absent.
- **Architecture boundary check**: `solera-execute-action-item` Step 4 enforces
  `architecture_rules` from team-process.md — greps for forbidden import patterns
  in changed files, blocks completion on violation
- **Layer-aware ACT decomposition**: `solera-write-story` Step 3 decomposes Action
  Items by architectural layer when `execution_order.groups` is defined, ensuring
  correct phase ordering from the start

### Changed
- **team-process.md template**: added `execution_order`, `architecture_rules` sections
  and extended `workflow_gates` to support structured `checks[]` array
- **solera-init interview**: added Step C-5 for automatable gate checks; added Step F
  questions for layered architecture ordering and boundary rules
- `solera-write-story` v8.0.0 → v9.0.0
- `solera-execute-action-item` v6.0.0 → v7.0.0

---

## [2.10.4] — 2026-03-20

### Fixed
- `solera-write-goal`: add missing `solera-create-pr` to `uses` array
- `solera-write-epic`: add missing `solera-create-pr` to `uses` array
- `solera-publish-artifacts`: fix description to reflect dual invocation (Goal Create + Epic Wrap-up)
- `solera-edit-rule`: normalize H1 from `# Skill: meta-rule` to `# Edit Rule`
- `solera-write-epic`: remove duplicate Directory Structure section

---

## [2.10.3] — 2026-03-20

### Added
- `user-invocable` frontmatter to all 16 skills (15 true, 1 false for solera-publish-artifacts)

---

## [2.10.2] — 2026-03-20

### Fixed
- `solera-create-pr`: metadata `type: composite` → `type: unit` (no sub-skill invocations)
- `solera-execute-action-item`: metadata `type: composite` → `type: unit` (no sub-skill invocations)
- `solera-init`: metadata `type: composite` → `type: unit` (no sub-skill invocations)

---

## [2.10.1] — 2026-03-18

### Fixed
- `solera-help`: metadata `type: reference` → `type: unit` (reference is not a valid type value)
- `solera-publish-artifacts`: metadata `type: composite` → `type: unit` (no sub-skill invocations)
- `solera-write-identity`: metadata `type: composite` → `type: unit` (no sub-skill invocations)

---

## [2.10.0] — 2026-03-18

### Removed
- **Handoff hook**: removed auto-HANDOFF.md generation — `git log` and `CLAUDE.md` provide sufficient context without extra API cost

---

## [2.9.2] — 2026-03-17

### Added
- **PRIVACY.md**: Privacy policy for marketplace submission — documents that Solera
  operates entirely locally with no data collection or external transmission

---

## [2.9.1] — 2026-03-17

### Added
- **LICENSE file**: MIT license added to plugin root for marketplace submission compliance

---

## [2.9.0] — 2026-03-16

### Changed (BREAKING)
- **Skill rename**: `solera-transition-catalog` → `solera-publish-artifacts` across all
  17 referencing files (SKILL.md, assets, docs, README). Directory renamed accordingly.

### Added
- **workflow_gates enforcement**: `solera-write-epic` and `solera-write-story` now read
  `team-process.md` and check gates before proceeding:
  - `epic.use_case` gate checked before Use Case step
  - `epic.concept` gate checked before Concept step
  - `story.execute` gate checked before Execute step
  - `story.wrap_up` gate checked before Wrap-up step
  - `solera-write-goal` also enforces unmet gates (blocking)
  - Previously gates were defined in team-process.md but never enforced (dead code)

### Fixed
- **Translate all remaining Korean to English**: Error Handling tables in 7 SKILL.md files,
  Examples sections in write-story and write-epic, 3 test files (test_skill_validation.py,
  test_handoff_hook.py, tests/README.md), and Korean trigger phrases removed from solera-help

---

## [2.8.1] — 2026-03-16

### Fixed
- **Translate all remaining Korean to English** across 3 files (58+ violations):
  - `solera-workflow.md`: Intent → Skill Routing table fully translated
  - `solera-write-identity`: persona interview questions (NN/G 6-field) + Error Handling table
  - `solera-write-goal`: BLOCKING comments, Error Handling table, and full Examples section

---

## [2.8.0] — 2026-03-16

### Changed (BREAKING)
- **`solera-init` SKILL.md fully rewritten in English** (v2.0.0)
  - All hardcoded Korean interview questions replaced with principle-based
    interview structure (Steps A–G), each mapped to a specific `team-process.md` field
  - Interview is now language-agnostic: AI asks in the user's language
- **`solera-init` Step 5 kickoff interview**: generalized from software-only to
  any project type (software / marketing / design / content / other)
  - Project type detected first; software projects get additional `tech_stack` fields
  - Stage list examples adapt to project type (software, marketing, design)
  - Every question traces to a specific output field (no orphan questions)

### Added
- **`assets/team-process-software.md`**: software development extension template
  (`tech_stack.backend`, `frontend`, `infra`) — merged into `team-process.md`
  when `project.type = "software"`
- **`team-process.md` base template**: redesigned as a universal project template
  with `project`, `workflow_gates`, `process_stages`, `conventions`, `tools`, `custom_rules`

---

## [2.7.2] — 2026-03-16

### Fixed
- **`solera-init` Step 5**: 나머지 4개 낮은 심각도 이슈 수정
  - UX vs UI 구분 설명 추가 — 체크리스트에 "(UX와 UI를 구분하지 않는다면 하나로 합쳐도 됨)" 안내
  - 백엔드/프론트 병렬 여부 질문 추가 — 둘 다 선택 시 "동시 진행인가요?" 확인
  - UI 디자인/엔티티 게이트 범위 명확화 — 프론트만 / 전체 개발 중 어느 쪽인지 질문
  - 배포 단계 심화 추가 — CI/CD, 배포 환경, 승인 절차 수집; 기술 스택 섹션에서 중복 방지
  - `workflow_gates` 템플릿 주석에 각 게이트의 적용 레벨(Epic/Story 범위) 명시

---

## [2.7.1] — 2026-03-16

### Fixed
- **`solera-init` Step 5 섹션 2**: 시뮬레이션 테스트에서 발견된 3개 이슈 수정
  - PR 승인 수 중복 수집 제거 — 코드 리뷰 단계(2-2)에서 수집한 값을 Section 4에서 재사용
  - `story.execute` 다중 게이트 조건 처리 추가 — 여러 gate=true 단계가 충돌 시
    백엔드/프론트 범위 확인 질문으로 AND 조건 분리 여부 결정
  - 초기 언급 단계가 최종 선택에서 누락된 경우 확인 질문 추가

---

## [2.7.0] — 2026-03-16

### Changed
- **`solera-init` Step 5 섹션 2**: "개발 프로세스" 인터뷰를 3단계 계층형 구조로 심화
  - 2-1: 팀이 실제로 사용하는 단계를 체크리스트 형식으로 선택
    (기획/UX/UI/엔티티/API/개발/테스트/리뷰/QA/배포)
  - 2-2: 선택된 단계에 대해서만 완료 기준, 툴, 담당자, 게이트 여부를 심화 질문
  - 2-3: AI가 수집한 답변으로 workflow_gates를 자동 도출 후 사용자 확인
- **`team-process.md` 템플릿**: `workflow_gates`에 4개 게이트 키 추가
  (`epic.use_case`, `epic.concept`, `story.execute`, `story.wrap_up`),
  `process_stages` 섹션 신규 추가 (단계별 name/tool/done_when/gate 구조)

---

## [2.6.0] — 2026-03-16

### Added
- **`solera-init`: Team Kickoff Interview** (Step 5) — conversational interview that
  collects service info, workflow gates, tech stack, and conventions, then generates
  `{project_path}/workspace/team-process.md`
- **`team-process.md` template** — YAML format with sections for service, workflow_gates,
  tech_stack, conventions, custom_rules; read by skills at Goal/Epic level

### Changed
- **`solera-workflow.md`** (installed rule) — rewritten as a slim Intent → Skill Routing
  table; removed procedural content; added pointer to `team-process.md`
- **`solera-write-identity`**: Step 1 expanded to Discovery Interview with NN/G 6-field
  persona model (role, skill level, context, goal, pain point, quote); personas are additive
- **`solera-write-goal`**: Journey step now creates new files per Goal (`{goal_id}-{persona}.md`)
  instead of overwriting — follows OCP (open for extension, closed for modification)

---

## [2.5.0] — 2026-03-16

### Added
- **Team Customization section** in `solera-workflow.md` template (installed by `solera-init`)
  - Teams can define workflow gates, artifact conventions, commit/branch conventions,
    tech stack, and custom rules on top of Solera's work item structure
  - Solera provides the skeleton; each team wraps it with their own process rules

---

## [2.4.0] — 2026-03-16

### Changed
- **Branch naming**: Epic branches changed from `epic-[name]` to `epics/[name]`.
  Story branches changed from `epic-[name]/story-[ID]-[name]` to
  `epics-[name]/story-[ID]-[name]` (avoids git file/directory conflict).
- Updated all branch references across skills, docs, and README

---

## [2.3.1] — 2026-03-16

### Fixed
- README.md: added missing `solera-init` and `solera-help` to Skills table
- solera-help SKILL.md: added self-reference to Meta skills listing

---

## [2.3.0] — 2026-03-16

### Changed (BREAKING)
- **Directory structure flattened**: Removed `stories/` and `action-items/`
  intermediate directories
  - Before: `epics/{name}/stories/US-001/action-items/ACT-001-xxx.md`
  - After: `epics/{name}/US-001-login-screen/ACT-001-xxx.md`
- Story folder naming now includes slug: `{story_id}-{story_name}/`
  (e.g., `US-001-login-screen/`) for readability
- Updated all path references across: write-story, write-epic, execute-action-item,
  manage-workflow, write-goal, architecture.md, quick-start.md

---

## [2.2.0] — 2026-03-16

### Added
- **solera-write-story**: Scan available project skills (`Glob .claude/skills/*/SKILL.md`
  and `.claude/plugins/*/skills/*/SKILL.md`) during Action Item decomposition
- **solera-write-story**: `Skill` column added to Action Items table — matches
  task content against scanned skill triggers
- **solera-execute-action-item**: `Skill Resolution` section — reads `Skill:`
  metadata from ACT file and auto-invokes the specified skill; falls back to
  keyword matching when set to `-`
- **action-item.md** template: `Skill:` metadata field added
- **story.md** template: `Skill` column added to Action Items tables (US & TS)

---

## [2.1.0] — 2026-03-16

### Added
- **solera-create-pr**: `target_branch` is now optional — resolved from
  `default_pr_base` in `.claude/rules/solera-workflow.md` Project Config,
  with fallback to user prompt
- **solera-create-pr**: Artifact promotion pre-check blocks PR creation when
  Epic-level artifacts (use-case, concept, erd, dto, api-spec) remain in
  `artifacts/` — instructs user to run `solera-transition-catalog` first
- **solera-workflow.md** template: added `## Project Config` section with
  `default_pr_base` setting (commented out by default)

---

## [2.0.0] — 2026-03-15

### Changed (BREAKING)
- All 16 skills renamed with `solera-` prefix to avoid name collisions with
  other plugins: `write-goal` → `solera-write-goal`, `create-pr` → `solera-create-pr`,
  `handoff` → `solera-handoff`, etc.
- Updated all internal references: SKILL.md files, asset templates, self-verification
  files, docs, README, tests, and handoff hook

---

## [1.11.0] — 2026-03-15

### Added
- `init` skill: sets up Solera in a new project — installs `.claude/rules/solera-workflow.md`
  (workflow rules, git branch conventions, artifact promotion, commit format) and creates
  the workspace folder structure with initial `progress.md`
- Updated `help` skill to list `init` and guide new users to run it first

---

## [1.10.0] — 2026-03-15

### Changed
- **Artifact promotion is now incremental** — `transition-catalog` is invoked at
  two points instead of once at Goal completion:
  1. After Goal Create: promotes Goal-level artifacts (service-map, persona, journey)
  2. At each Epic Wrap-up: promotes Epic-level artifacts (use-case, concept)
- Goal Wrap-up no longer calls `transition-catalog`; it only confirms `artifacts/`
  is empty
- `write-epic` now includes `transition-catalog` in its `uses` and Wrap-up procedure
- Updated all docs, templates, self-verification files, and error handling to reflect
  the incremental promotion model

---

## [1.9.7] — 2026-03-15

### Fixed
- Fix stale skill name references across all docs, SKILL.md, asset templates,
  and self-verification files. Align with v1.5.0 rename: `writing-*` → `write-*`,
  `writing-action-item` → `execute-action-item`, `workflow-manage` → `manage-workflow`,
  `workflow-pr` → `create-pr`, `catalog-transition` → `transition-catalog`.

---

## [1.9.6] — 2026-03-08

### Fixed
- `handoff_hook.py`: add project scope guard — only run in the plugin's
  home project (noory-ai), skip other projects like flutter-material-kit
  that have solera enabled. Prevents spurious handoff sessions in unrelated
  project session folders.

---

## [1.9.5] — 2026-03-08

### Fixed
- `handoff_hook.py`: replace ephemeral lockfile with TTL-based lock (120s).
  Previous lockfile was deleted in `finally`, allowing queued SessionEnd hooks
  to re-enter immediately after cleanup. Now the lock persists for 120s after
  creation, blocking all re-entrant calls during that window.

---

## [1.9.4] — 2026-03-08

### Fixed
- `handoff_hook.py`: replace env var guard with lockfile (`/tmp/solera-handoff-hook.lock`)
  Env vars are not propagated into hook subprocesses by Claude Code, so the previous
  `SOLERA_HANDOFF_RUNNING` guard had no effect. Lockfile approach reliably prevents
  concurrent re-entrant invocations.

---

## [1.9.3] — 2026-03-08

### Fixed
- `handoff_hook.py`: add `SOLERA_HANDOFF_RUNNING` env guard to prevent recursive
  SessionEnd invocations — `claude -p` subprocesses also trigger SessionEnd,
  causing HANDOFF.md to be overwritten repeatedly and processes to accumulate

---

## [1.9.2] — 2026-03-07

### Improved
- Standardized `| Step | Output | Path | Nature |` table format across all skills
- Added `execution_model` metadata and blocking/non-blocking clarification to write-goal, write-epic, write-story, manage-workflow
- Unified sub-skill invocation syntax to `Skill(name="...", args={...})` in write-epic, write-goal, write-story
- Added end-to-end `## Examples` sections to write-epic, write-goal, write-story
- `refactor`: aligned transition-catalog parameters with write-goal/epic/story pattern
- `refactor`: standardized hierarchical parameter naming across all skills
- `docs`: added `## Error Handling` section to all skills
- `test`: added automated skill parameter validation tests (9 cases)

---

## [1.9.1] — 2026-03-07

### Fixed
- `handoff_hook.py`: replace `Popen` + `start_new_session=True` with `subprocess.run(timeout=60)`
  `start_new_session` has no effect on macOS (setsid not supported), leaving orphan processes
  on every SessionEnd. Blocking run ensures clean process lifecycle.

---

## [1.4.0] - 2026-03-02

### Changed
- Renamed 13 skills to verb-first naming for clarity and intent:
  - `writing-*` → `write-*` (identity, phase, goal, epic, story)
  - `writing-action-item` → `execute-action-item`
  - `workflow-manage` → `manage-workflow`
  - `workflow-pr` → `create-pr`
  - `catalog-transition` → `transition-catalog`
  - `meta-skill` → `edit-skill`, `meta-rule` → `edit-rule`, `meta-command` → `edit-command`, `meta-subagent` → `edit-agent`
- Expanded triggers from 3–4 noun phrases to 5–6 natural English verb phrases per skill
- Rewrote all skill descriptions from internal-impl view to user-outcome view

## [1.3.0] - 2026-03-02

### Added
- `meta-skill` skill: create, review, or improve skill files in `.claude/skills/`; includes 4 type templates (unit-guide, unit-procedural, composite-guide, composite-procedural)
- `meta-rule` skill: create, review, or improve rule files in `.claude/rules/`
- `meta-command` skill: create, review, or improve slash command files in `.claude/commands/`
- `meta-subagent` skill: create, review, or improve agent definition files in `.claude/agents/`
- `docs/work-item-structure.md`: full hierarchy diagram (Identity → Action Item), folder layout, branch mapping, Human vs AI responsibility split

## [1.2.0] - 2026-03-02

### Added
- `writing-identity` skill: define service identity (Mission, Core Values, Vision, Goals rough list)

## [1.1.0] - 2026-03-02

### Added
- `docs/` folder with quick-start, architecture, and team-workflow guides
- README rewritten with Why Solera, Quick Start, comparison table, and team workflow section

### Changed
- plugin.json: version 1.1.0, expanded keywords

## [1.0.0] - 2026-03-01

### Added
- Initial release with 9 workflow skills
- Writing hierarchy: writing-phase, writing-goal, writing-epic, writing-story, writing-action-item
- Workflow management: workflow-manage, workflow-pr
- Context management: catalog-transition, handoff
- Stop hook: auto-runs handoff skill on session end
