# Changelog

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
