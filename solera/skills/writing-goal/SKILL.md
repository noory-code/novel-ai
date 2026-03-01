---
name: writing-goal
description: Goal 문서 작성. Service Map, Persona, Journey(러프) 생성 → Epic 분해.
metadata:
  version: "4.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [Goal 상세화, Goal 시작, Epic으로 분해]
  uses: [writing-identity, writing-epic, catalog-transition]
---

# Writing Goal

> _goal.md를 작성하고, Epic으로 분해한다.

## 선행조건

- `published/identity/mission.md` 존재 → 없으면 writing-identity invoke
- Phase README에 해당 Goal이 배정되어 있을 것 → 없으면 writing-phase invoke

## 입력

| 파라미터 | 필수 | 설명 | 예시 |
|----------|------|------|------|
| **goal_id** | Y | Goal ID | G1 |
| **goal_name** | Y | Goal 이름 | search-liquor |
| **goal_type** | N | Feature \| Enabler (기본: Feature) | Enabler |
| **project_path** | Y | 프로젝트 workspace 루트 | banas/workspace |
| **phase_id** | Y | 소속 Phase ID | 2026-P1-foundation |

## 산출물

| Step | 산출물 | 경로 |
|------|--------|------|
| Create | _goal.md | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/_goal.md` |
| Create | Service Map (Feature만) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/service-map/index.md` |
| Create | Persona (Feature만) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/persona/*.md` |
| Create | Persona Relationship (Feature, 2명+) | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/artifacts/persona/relationship.md` |
| Execute | Epic 문서 | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/epics/{NN}-{name}/_epic.md` |
| Wrap-up | RETRO.md | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/RETRO.md` |

## 사용 스킬

| 스킬 | 용도 | Step |
|------|------|------|
| `writing-identity` | identity 미존재 시 생성 | Setup |
| `writing-epic` | 각 Epic 상세화 및 Story 분해 | Execute |
| `catalog-transition` | artifacts → catalog 이동 | Wrap-up |

## 절차

1. **Setup**
   - [ ] `published/identity/mission.md` 존재 확인 → 없으면 writing-identity invoke
   - [ ] Phase README에서 해당 Goal 정보 확인 (기간, 목표)
   - [ ] `goals/{goal_id}-{name}/` 폴더 생성
   - [ ] `goals/{goal_id}-{name}/artifacts/` 폴더 생성

2. **Goal 유형 확인**
   - Feature → 3단계부터 순서대로
   - Enabler → 3단계 건너뜀, 4단계에서 Journey는 Steps만 간략 작성

3. **Service Map, Persona 생성** (Feature만)
   - [ ] Service Map 작성 → ref: [assets/service-map.md](assets/service-map.md)
   - [ ] Persona 프로필, 목표, Pain Points → ref: [assets/persona.md](assets/persona.md)
   - [ ] Persona 2명 이상이면 persona-relationship.md 생성 → ref: [assets/persona-relationship.md](assets/persona-relationship.md)

4. **Journey + Epic 분해 + _goal.md 작성**
   - [ ] Persona별 Journey 정의 (Enabler는 Steps만 간략 작성)
   - [ ] Journey → Epic 매핑, 번호 부여 (01, 02, ...)
   - [ ] _goal.md 작성 → ref: [assets/goal-template.md](assets/goal-template.md)

5. **Execute**
   - [ ] 각 Epic에 writing-epic invoke (Setup → Create → Execute → Wrap-up)
   - [ ] Epic 완료 시 workflow-pr invoke → 부모 브랜치로 PR
   - [ ] 모든 Epic 완료 확인

6. **Goal Wrap-up**
   - [ ] 모든 Epic 상태 ✅ 확인
   - [ ] RETRO.md 작성 → ref: [assets/retro.md](assets/retro.md)
   - [ ] catalog-transition invoke (artifacts/ → published/)
   - [ ] _goal.md 상태 → ✅

## 폴더 구조

```
{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/
├── _goal.md
├── RETRO.md          # Wrap-up 시 생성
├── artifacts/
│   ├── service-map/index.md    # Feature만
│   └── persona/*.md            # Feature만
└── epics/{NN}-{name}/
    └── _epic.md
```

## Completion Checklist

- [ ] _goal.md 생성 완료
- [ ] Feature인 경우: Service Map, Persona 생성
- [ ] Feature + Persona 2명 이상: persona-relationship.md 생성
- [ ] Journey (러프) 작성
- [ ] Epic 분해 완료
- [ ] (Execute) 모든 Epic에 writing-epic invoke 완료
- [ ] (Wrap-up) RETRO.md 작성
- [ ] (Wrap-up) catalog-transition 완료
- [ ] (Wrap-up) _goal.md 상태 ✅
