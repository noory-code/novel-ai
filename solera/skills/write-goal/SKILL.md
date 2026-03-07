---
name: write-goal
description: Define what success looks like for a Goal — map the service, identify personas, sketch the journey, and break it into Epics.
metadata:
  version: "5.0.0"
  category: writing
  type: composite
  style: procedural
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
| **goal_id** | Y | Goal ID | G1 |
| **goal_name** | Y | Goal name | search-liquor |
| **goal_type** | N | Feature \| Enabler (default: Feature) | Enabler |
| **project_path** | Y | Project workspace root | banas/workspace |
| **phase_id** | Y | Parent Phase ID | 2026-P1-foundation |

## Output

| Step | Output | Path |
|------|--------|------|
| Create | _goal.md | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/_goal.md` |
| Create | Service Map (Feature only) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/service-map/index.md` |
| Create | Persona (Feature only) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/persona/*.md` |
| Create | Persona Relationship (Feature, 2+ personas) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/persona/relationship.md` |
| Execute | Epic document | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/epics/{NN}-{name}/_epic.md` |
| Wrap-up | RETRO.md | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/RETRO.md` |

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `writing-identity` | Create identity if it does not exist | Setup |
| `writing-epic` | Elaborate each Epic and decompose it into Stories | Execute |
| `catalog-transition` | Move artifacts/ to published/ | Wrap-up |

## Procedure

1. **Setup**
   - [ ] Confirm `published/identity/mission.md` exists; if not, invoke writing-identity
   - [ ] Confirm `{project_path}/phase/{phase_id}/README.md` exists with Glob tool
     - If not: invoke Skill tool `skill="write-phase"` with args:
       `project_path={project_path}, phase_id={phase_id}, year={first 4 chars of phase_id}` → resume after completion
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
   - [ ] Invoke writing-epic for each Epic (Setup → Create → Execute → Wrap-up)
   - [ ] Invoke workflow-pr upon Epic completion to create a PR to the parent branch
   - [ ] Confirm all Epics are complete

6. **Goal Wrap-up**
   - [ ] Confirm all Epic statuses ✅
   - [ ] Write RETRO.md — ref: [assets/retro.md](assets/retro.md)
   - [ ] Invoke catalog-transition (artifacts/ to published/)
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
