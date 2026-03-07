---
name: write-epic
description: Scope an Epic — write use cases, define the concept, and decompose into Stories ready to implement.
metadata:
  version: "5.0.0"
  category: writing
  type: composite
  style: procedural
  execution_model: sequential
  triggers: [write an Epic, plan an Epic, start an Epic, break Epic into Stories, define Epic scope, draft concept]
  uses: [write-story]
---

# Writing Epic

> Writes _epic.md and decomposes the Epic into Stories.

## Prerequisites

- `published/identity/mission.md` exists
  - If not: check `published/identity/mission.md` with Glob tool → invoke `writing-identity` with Skill tool
- `_goal.md` exists
  - If not: check `{goal_path}/_goal.md` with Glob tool → invoke `write-goal` with Skill tool passing:
    `goal_id={goal_id}, goal_name={goal_id}, project_path={project_path}, phase_id={phase_id}`
    (ask user to confirm `goal_name` if it differs from `goal_id`)
  - If `phase_id` is unknown: ask the user before proceeding
  - New project: run `write-identity` first to establish `identity/` and `initiative/{year}/goals.md`
- The corresponding Epic must be assigned in _goal.md

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas/workspace |
| **year** | Y | Initiative year | 2026 |
| **phase_id** | Y | Parent Phase ID | 2026-P1-foundation |
| **goal_id** | Y | Parent Goal ID | G1 |
| **goal_name** | Y | Parent Goal name | search-liquor |
| **epic_name** | Y | Epic name | 01-auth |
| **epic_type** | N | Feature \| Enabler (default: Feature) | Enabler |

## Output

| Step | Output | Nature | Path |
|------|--------|--------|------|
| Setup | _epic.md | Final | `{goal_path}/epics/{epic_name}/_epic.md` |
| UseCase | UC-NNN.md (Feature only) | Intermediate (artifacts) | `{goal_path}/artifacts/use-case/UC-NNN-{name}.md` |
| Concept | domain.md | Intermediate (artifacts) | `{goal_path}/artifacts/concept/domain.md` |
| Concept | entities/*.md | Intermediate (artifacts) | `{goal_path}/artifacts/concept/entities/{entity}.md` |
| Story | _story.md | Final | `{goal_path}/epics/{epic_name}/stories/{US\|TS}-NNN/_story.md` |
| Wrap-up | RETRO.md | Final | `{goal_path}/epics/{epic_name}/RETRO.md` |

> `{goal_path}` = `{project_path}/phase/{phase_id}/goals/{goal_id}`
> artifacts = intermediate outputs. Moved to published/ via catalog-transition upon Goal completion.

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `writing-story` | Elaborate each Story and decompose it into Action Items | Execute |
| `workflow-pr` | Create a PR upon Story/Epic completion | Execute, Wrap-up |

## Procedure

1. **Setup**
   - [ ] Confirm `{goal_path}/_goal.md` exists with Glob tool
     - If not: `Skill(name="write-goal", args={"project_path": "{project_path}", "year": "{year}", "phase_id": "{phase_id}", "goal_id": "{goal_id}", "goal_name": "{goal_name}", "goal_type": "{goal_type 또는 기본값 Feature}"})`
       (ask user to confirm `goal_name` if it differs from `goal_id`) **(BLOCKING: Goal 생성 완료 후 재개)**
   - [ ] Create `epic-{epic_name}` branch (from Goal branch)
   - [ ] Create `{goal_path}/epics/{epic_name}/` folder
   - [ ] Create _epic.md draft — ref: [assets/epic-template.md](assets/epic-template.md)
   - [ ] Status → 🔄

2. **Create Use Case** (Feature only, skip for Enabler)
   - [ ] Define the Actor (person or system)
   - [ ] Define the Goal (measurable objective)
   - [ ] Write the basic flow (step by step)
   - [ ] Write alternative and exception flows
   - [ ] Ref: [assets/use-case.md](assets/use-case.md)

3. **Create Concept**
   - [ ] Derive core concepts, then write or update domain.md — ref: [assets/concept.md](assets/concept.md)
   - [ ] Write a detailed description for each Entity — ref: [assets/entity.md](assets/entity.md)
   - [ ] Add a relationship diagram (Mermaid classDiagram)
   - domain.md rule: the first Epic creates it; subsequent Epics **update** it rather than overwrite it
   - concept.md = full version template, entity.md = quick reference skeleton

4. **Story decomposition and complete _epic.md**
   - [ ] Map Use Cases to Stories (Feature) or technical tasks to Stories (Enabler)
   - [ ] Assign Story IDs (US: User Story, TS: Technical Story)
   - [ ] Estimate the expected commit count for each Story
   - [ ] Complete the Stories table in _epic.md and define completion criteria

5. **Execute**
   - [ ] Extract incomplete (⏳ or no status) Stories from the Stories table in `_epic.md`
   - [ ] Execute each Story in order **(BLOCKING: 각 Story가 완료될 때까지 대기, 순차적으로 실행)**:
     ```python
     Skill(name="write-story", args={
       "project_path": "{project_path}",
       "year": "{year}",
       "phase_id": "{phase_id}",
       "goal_id": "{goal_id}",
       "goal_name": "{goal_name}",
       "epic_name": "{epic_name}",
       "epic_type": "{epic_type}",
       "story_id": "{US|TS-NNN}",
       "story_name": "{name}",
       "story_type": "{US|TS}"
     })
     → Confirm _story.md created + status ✅ before proceeding to next Story
     ```
   - [ ] Merge to the Epic branch upon Story completion
   - [ ] Proceed to Step 6 after confirming all Story statuses ✅

6. **Wrap-up**
   - [ ] Confirm all Story statuses ✅ (return to Step 5 if any are incomplete)
   - [ ] Write RETRO.md — ref: [assets/retro.md](assets/retro.md)
   - [ ] Set _epic.md status to ✅
   - [ ] `Skill(name="create-pr")` **(BLOCKING: PR 생성 완료 후 스킬 종료)** → create PR to parent branch (Goal)

## Directory Structure

Epics always live inside the goal directory. Never create a top-level `epics/` directory.

```
{project_path}/phase/{phase_id}/goals/{goal_id}/   ← created by write-goal
├── _goal.md
├── artifacts/
└── epics/{epic_name}/                              ← created by write-epic
    ├── _epic.md
    └── stories/{US|TS}-NNN/
        └── _story.md
```

## Folder Structure

```
{goal_path}/
├── artifacts/                # Intermediate outputs
│   ├── use-case/UC-NNN-{name}.md
│   └── concept/
│       ├── domain.md
│       └── entities/{entity}.md
└── epics/{epic_name}/
    ├── _epic.md
    ├── RETRO.md              # Created at Wrap-up
    └── stories/{US|TS}-NNN/
        └── _story.md
```

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| mission.md 누락 | `published/identity/mission.md` 없음 | Glob으로 확인 후 Skill tool로 `write-identity` 호출 | identity 생성 후 이 스킬 재개 |
| _goal.md 누락 | `{goal_path}/_goal.md` 없음 | Glob으로 확인 후 Skill tool로 `write-goal` 호출 (project_path, year, phase_id, goal_id, goal_name, goal_type 전달, 사용자에게 goal_name 확인) | Goal 생성 후 이 스킬 재개 |
| phase_id 불명 | phase_id 파라미터 없음 | 사용자에게 phase_id 입력 요청 | 파라미터 입력될 때까지 중단 |
| Epic 미할당 | _goal.md에 Epic 정보 없음 | 오류 메시지 출력, _goal.md 업데이트 요청 | 스킬 중단, 수동 수정 후 재개 |
| 브랜치 생성 실패 | git 오류 (충돌, 권한 등) | git 오류 메시지 출력, 수동 해결 요청 | 스킬 중단, 해결 후 재개 |
| domain.md 업데이트 충돌 | 기존 domain.md와 새 내용 충돌 | 병합 필요 영역 표시, 사용자에게 수동 병합 요청 | Concept 단계 중단, 수동 병합 후 재개 |
| writing-story 실패 | 하위 스킬 호출 실패 | 실패한 Story 기록, 사용자에게 알림 | 해당 Story 건너뛰고 계속 진행 또는 중단 |
| workflow-pr 실패 | PR 생성 실패 | PR 생성 오류 출력, 수동 PR 생성 요청 | Wrap-up 중단, 수동 PR 생성 후 완료 |

## Examples

### 예시: Feature Epic 전체 실행 과정

#### 스킬 호출

```python
Skill(name="write-epic", args={
  "project_path": "/Users/myname/workspace/myapp",
  "year": "2026",
  "phase_id": "2026-P1-foundation",
  "goal_id": "G1",
  "goal_name": "search-liquor",
  "epic_name": "01-search-ui",
  "epic_type": "Feature"
})
```

#### 실행 단계별 생성 파일

**1. Setup 완료 후**
```
goals/G1-search-liquor/epics/01-search-ui/
└── _epic.md              (초안, 상태: 🔄)
```

**2. Use Case 생성 완료 후**
```
goals/G1-search-liquor/
├── artifacts/
│   └── use-case/
│       ├── UC-001-basic-search.md
│       └── UC-002-filter-search.md
└── epics/01-search-ui/
    └── _epic.md
```

**3. Concept 생성 완료 후**
```
goals/G1-search-liquor/
├── artifacts/
│   ├── use-case/...
│   └── concept/
│       ├── domain.md
│       └── entities/
│           ├── search-query.md
│           ├── filter.md
│           └── result-set.md
└── epics/01-search-ui/
    └── _epic.md
```

**4. Story 분해 완료 후 (_epic.md 업데이트)**
```markdown
# _epic.md

...
## Stories

| ID | Name | UC | Commits | Status |
|----|------|----|---------|--------|
| US-001 | search-input | UC-001 | 3 | ⏳ |
| US-002 | filter-ui | UC-002 | 2 | ⏳ |
| TS-001 | api-integration | - | 4 | ⏳ |
```

**5. Execute 중간 상태 (Story US-001 완료)**
```
goals/G1-search-liquor/epics/01-search-ui/
├── _epic.md              (US-001: ✅, US-002: 🔄, TS-001: ⏳)
└── stories/
    ├── US-001/
    │   ├── _story.md     (상태: ✅)
    │   ├── RETRO.md
    │   └── action-items/
    │       ├── ACT-001-create-component.md
    │       ├── ACT-002-add-validation.md
    │       └── ACT-003-write-tests.md
    └── US-002/
        ├── _story.md     (상태: 🔄)
        └── action-items/...
```

**6. Wrap-up 완료 (모든 Story ✅)**
```
goals/G1-search-liquor/epics/01-search-ui/
├── _epic.md              (상태: ✅)
├── RETRO.md
└── stories/
    ├── US-001/...        (✅)
    ├── US-002/...        (✅)
    └── TS-001/...        (✅)
```

#### 중간에 호출되는 하위 스킬

```python
# Story US-001 작성
Skill(name="write-story", args={
  "project_path": "/Users/myname/workspace/myapp",
  "year": "2026",
  "phase_id": "2026-P1-foundation",
  "goal_id": "G1",
  "goal_name": "search-liquor",
  "epic_name": "01-search-ui",
  "epic_type": "Feature",
  "story_id": "US-001",
  "story_name": "search-input",
  "story_type": "US"
})
# → _story.md 생성, Action Items 분해, 모든 ACT 실행 후 ✅

# Story US-002, TS-001 반복...

# Epic 완료 후 PR 생성
Skill(name="create-pr")
# → Epic 브랜치에서 Goal 브랜치로 PR
```

#### 최종 출력 상태

- `_epic.md` 상태: ✅
- 모든 Story 상태: ✅
- `RETRO.md` 존재
- PR이 Goal 브랜치로 생성됨

## Completion Checklist

- [ ] _epic.md created
- [ ] If Feature: Use Case written
- [ ] Concept (domain.md, entities) written or updated
- [ ] Story decomposition complete
- [ ] (Execute) writing-story invoked for all Stories
- [ ] (Wrap-up) RETRO.md written
- [ ] (Wrap-up) _epic.md status ✅
- [ ] (Wrap-up) workflow-pr invoked
