---
name: write-goal
description: Define what success looks like for a Goal — map the service, identify personas, sketch the journey, and break it into Epics.
metadata:
  version: "5.0.0"
  category: writing
  type: composite
  style: procedural
  execution_model: sequential
  triggers: [write a Goal, start a Goal, plan a Goal, break Goal into Epics, elaborate on a Goal]
  uses: [write-identity, write-epic, transition-catalog]
---

# Writing Goal

> Writes the _goal.md file and decomposes the Goal into Epics.

## Prerequisites

- `published/identity/mission.md` exists; if not, invoke writing-identity
- The corresponding Goal must be assigned in the Phase README
  - If not: invoke `write-phase` with Skill tool passing:
    `project_path={project_path}, phase_id={phase_id}, year={first 4 chars of phase_id, e.g. "2026-P1-foundation" → "2026"}`

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas/workspace |
| **year** | Y | Initiative year | 2026 |
| **phase_id** | Y | Parent Phase ID | 2026-P1-foundation |
| **goal_id** | Y | Goal ID | G1 |
| **goal_name** | Y | Goal name | search-liquor |
| **goal_type** | N | Feature \| Enabler (default: Feature) | Enabler |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create | _goal.md | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/_goal.md` | Final |
| Create | Service Map (Feature only) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/service-map/index.md` | Intermediate |
| Create | Persona (Feature only) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/persona/*.md` | Intermediate |
| Create | Persona Relationship (Feature, 2+ personas) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/persona/relationship.md` | Intermediate |
| Execute | Epic document | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/epics/{NN}-{name}/_epic.md` | Final |
| Wrap-up | RETRO.md | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/RETRO.md` | Final |

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `writing-identity` | Create identity if it does not exist | Setup |
| `writing-epic` | Elaborate each Epic and decompose it into Stories | Execute |
| `catalog-transition` | Move artifacts/ to published/ | Wrap-up |

## Procedure

1. **Setup**
   - [ ] Confirm `published/identity/mission.md` exists; if not, invoke writing-identity **(BLOCKING: 현재 스킬은 일시 중지되고 identity 생성 완료 후 재개)**
   - [ ] Confirm `{project_path}/phase/{phase_id}/README.md` exists with Glob tool
     - If not: `Skill(name="write-phase", args={"project_path": "{project_path}", "year": "{year}", "phase_id": "{phase_id}"})` **(BLOCKING: Phase 생성 완료 후 재개)**
   - [ ] Confirm Goal information from the Phase README (period, objectives)
   - [ ] Create `goals/{goal_id}-{name}/` folder
   - [ ] Create `goals/{goal_id}-{name}/artifacts/` folder

2. **Confirm Goal type**
   - For Features, proceed in order from Step 3
   - For Enablers, skip Step 3 and write the Journey as Steps only (briefly) in Step 4

3. **Create Service Map and Personas** (Feature only)
   - [ ] Write the Service Map — ref: [assets/service-map.md](assets/service-map.md)
   - [ ] Write Persona profile, goals, and Pain Points — ref: [assets/persona.md](assets/persona.md)
   - [ ] If there are 2 or more Personas, create persona-relationship.md — ref: [assets/persona-relationship.md](assets/persona-relationship.md)

4. **Journey, Epic decomposition, and _goal.md**
   - [ ] Define a Journey for each Persona (for Enablers, write Steps only, briefly)
   - [ ] Map Journey steps to Epics and assign numbers (01, 02, ...)
   - [ ] Write _goal.md — ref: [assets/goal-template.md](assets/goal-template.md)

5. **Execute**
   - [ ] Invoke writing-epic for each Epic (Setup → Create → Execute → Wrap-up) **(BLOCKING: 각 Epic이 완료될 때까지 대기, 순차적으로 실행)**
   - [ ] Invoke workflow-pr upon Epic completion to create a PR to the parent branch **(BLOCKING: PR 생성 완료 후 다음 Epic으로 진행)**
   - [ ] Confirm all Epics are complete

6. **Goal Wrap-up**
   - [ ] Confirm all Epic statuses ✅
   - [ ] Write RETRO.md — ref: [assets/retro.md](assets/retro.md)
   - [ ] Invoke catalog-transition (artifacts/ to published/) **(BLOCKING: 카탈로그 전환 완료 후 상태 변경)**
   - [ ] Set _goal.md status to ✅

## Folder Structure

```
{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/
├── _goal.md
├── RETRO.md          # Created at Wrap-up
├── artifacts/
│   ├── service-map/index.md    # Feature only
│   └── persona/*.md            # Feature only
└── epics/{NN}-{name}/
    └── _epic.md
```

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| mission.md 누락 | `published/identity/mission.md` 없음 | Skill tool로 `write-identity` 호출 | identity 생성 후 이 스킬 재개 |
| Phase README 없음 | `phase/{phase_id}/README.md` 없음 | Skill tool로 `write-phase` 호출 (project_path, phase_id, year 전달) | Phase 생성 후 이 스킬 재개 |
| Goal 미할당 | Phase README에 Goal 정보 없음 | 오류 메시지 출력, Phase README 업데이트 요청 | 스킬 중단, 수동 수정 후 재개 |
| goal_type 불명확 | Feature/Enabler 구분 불가 | 기본값 Feature로 진행, 사용자에게 확인 요청 | 사용자 확인 후 필요 시 수정 |
| 폴더 생성 실패 | 권한 오류 또는 경로 문제 | 오류 메시지 출력, 권한 확인 요청 | 스킬 중단, 오류 상태 반환 |
| writing-epic 실패 | 하위 스킬 호출 실패 | 실패한 Epic 기록, 사용자에게 알림 | 해당 Epic 건너뛰고 계속 진행 또는 중단 |
| catalog-transition 실패 | artifacts 이동 실패 | 실패한 파일 목록 출력, 수동 이동 요청 | Wrap-up 중단, 수동 처리 후 재개 |

## Examples

### 예시: Feature Goal 전체 실행 과정

#### 스킬 호출

```python
Skill(name="write-goal", args={
  "project_path": "/Users/myname/workspace/myapp",
  "year": "2026",
  "phase_id": "2026-P1-foundation",
  "goal_id": "G1",
  "goal_name": "search-liquor",
  "goal_type": "Feature"
})
```

#### 실행 단계별 생성 파일

**1. Setup 완료 후**
```
phase/2026-P1-foundation/goals/G1-search-liquor/
├── _goal.md              (초안, 상태: 🔄)
└── artifacts/            (빈 폴더)
```

**2. Service Map & Personas 완료 후**
```
phase/2026-P1-foundation/goals/G1-search-liquor/
├── _goal.md
└── artifacts/
    ├── service-map/
    │   └── index.md
    └── persona/
        ├── bartender.md
        ├── liquor-enthusiast.md
        └── relationship.md
```

**3. Epic 분해 완료 후 (_goal.md 업데이트)**
```markdown
# _goal.md

...
## Epics

| ID | Name | Journey Step | Status |
|----|------|--------------|--------|
| 01 | search-ui | 검색창 입력 | ⏳ |
| 02 | filter-logic | 필터 적용 | ⏳ |
| 03 | result-display | 결과 확인 | ⏳ |
```

**4. Execute 중간 상태 (Epic 01 완료)**
```
phase/2026-P1-foundation/goals/G1-search-liquor/
├── _goal.md              (Epic 01: ✅, Epic 02: 🔄, Epic 03: ⏳)
├── artifacts/
│   ├── service-map/
│   └── persona/
└── epics/
    ├── 01-search-ui/
    │   ├── _epic.md      (상태: ✅)
    │   ├── RETRO.md
    │   └── stories/...
    └── 02-filter-logic/
        ├── _epic.md      (상태: 🔄)
        └── stories/...
```

**5. Wrap-up 완료 (모든 Epic ✅)**
```
phase/2026-P1-foundation/goals/G1-search-liquor/
├── _goal.md              (상태: ✅)
├── RETRO.md
└── epics/
    ├── 01-search-ui/...  (✅)
    ├── 02-filter-logic/...(✅)
    └── 03-result-display/...(✅)

published/
└── goal/
    ├── service-map/      (artifacts에서 이동)
    └── persona/          (artifacts에서 이동)
```

#### 중간에 호출되는 하위 스킬

```python
# Epic 01 작성
Skill(name="write-epic", args={
  "project_path": "/Users/myname/workspace/myapp",
  "year": "2026",
  "phase_id": "2026-P1-foundation",
  "goal_id": "G1",
  "goal_name": "search-liquor",
  "epic_name": "01-search-ui"
})
# → _epic.md 생성, stories 분해, 모든 Story 완료 후 ✅

# Epic 01 PR 생성
Skill(name="create-pr")
# → Epic 브랜치에서 Goal 브랜치로 PR

# Epic 02, 03 반복...

# Goal 완료 후 아티팩트 전환
Skill(name="transition-catalog")
# → artifacts/ → published/goal/
```

#### 최종 출력 상태

- `_goal.md` 상태: ✅
- 모든 Epic 상태: ✅
- `RETRO.md` 존재
- `artifacts/` 폴더 비어있음 (published/로 이동됨)

## Completion Checklist

- [ ] _goal.md created
- [ ] If Feature: Service Map and Personas created
- [ ] If Feature with 2 or more Personas: persona-relationship.md created
- [ ] Preliminary Journey written
- [ ] Epic decomposition complete
- [ ] (Execute) writing-epic invoked for all Epics
- [ ] (Wrap-up) RETRO.md written
- [ ] (Wrap-up) catalog-transition complete
- [ ] (Wrap-up) _goal.md status ✅
