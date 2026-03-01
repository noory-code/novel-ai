---
name: writing-epic
description: Epic 문서 작성. Use Case, Concept 생성 → Story 분해.
metadata:
  version: "4.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [Epic 상세화, Epic 시작, Story로 분해, Use Case, Concept]
  uses: [writing-story]
---

# Writing Epic

> _epic.md를 작성하고, Story로 분해한다.

## 선행조건

- `published/identity/mission.md` 존재
  - 없으면: Glob tool로 `published/identity/mission.md` 확인 → Skill tool로 `writing-identity` invoke
- `_goal.md` 존재
  - 없으면: Glob tool로 `{goal_path}/_goal.md` 확인 → Skill tool로 `writing-goal` invoke
- _goal.md에 해당 Epic이 배정되어 있을 것

## 입력

| 파라미터 | 필수 | 설명 | 예시 |
|----------|------|------|------|
| **project_path** | Y | 프로젝트 workspace 루트 | banas/workspace |
| **phase_id** | Y | 소속 Phase ID | 2026-P1-foundation |
| **goal_id** | Y | 소속 Goal ID | G1-search-liquor |
| **epic_name** | Y | Epic 이름 | 01-auth |
| **epic_type** | N | Feature \| Enabler (기본: Feature) | Enabler |

## 산출물

| Step | 산출물 | 성격 | 경로 |
|------|--------|------|------|
| Setup | _epic.md | 최종 | `{goal_path}/epics/{epic_name}/_epic.md` |
| UseCase | UC-NNN.md (Feature만) | 중간 (artifacts) | `{goal_path}/artifacts/use-case/UC-NNN-{name}.md` |
| Concept | domain.md | 중간 (artifacts) | `{goal_path}/artifacts/concept/domain.md` |
| Concept | entities/*.md | 중간 (artifacts) | `{goal_path}/artifacts/concept/entities/{entity}.md` |
| Story | _story.md | 최종 | `{goal_path}/epics/{epic_name}/stories/{US\|TS}-NNN/_story.md` |
| Wrap-up | RETRO.md | 최종 | `{goal_path}/epics/{epic_name}/RETRO.md` |

> `{goal_path}` = `{project_path}/phase/{phase_id}/goals/{goal_id}`
> artifacts = 중간 산출물. Goal 완료 시 catalog-transition으로 published/에 이동됨.

## 사용 스킬

| 스킬 | 용도 | Step |
|------|------|------|
| `writing-story` | 각 Story 상세화 및 Action Item 분해 | Execute |
| `workflow-pr` | Story/Epic 완료 시 PR 생성 | Execute, Wrap-up |

## 절차

1. **Setup**
   - [ ] Glob tool로 `{goal_path}/_goal.md` 존재 확인
     - 없으면: Skill tool `skill="writing-goal"` invoke → 완료 후 이 Step 재개
   - [ ] `epic-{epic_name}` 브랜치 생성 (from Goal 브랜치)
   - [ ] `{goal_path}/epics/{epic_name}/` 폴더 생성
   - [ ] _epic.md 초안 생성 → ref: [assets/epic-template.md](assets/epic-template.md)
   - [ ] 상태 → 🔄

2. **Use Case 생성** (Feature만, Enabler는 건너뜀)
   - [ ] Actor 정의 (사람/시스템)
   - [ ] Goal 정의 (측정 가능한 목표)
   - [ ] 기본 흐름 작성 (단계별)
   - [ ] 대안/예외 흐름 작성
   - [ ] → ref: [assets/use-case.md](assets/use-case.md)

3. **Concept 생성**
   - [ ] 핵심 개념 도출, domain.md 작성/업데이트 → ref: [assets/concept.md](assets/concept.md)
   - [ ] Entity별 상세 작성 → ref: [assets/entity.md](assets/entity.md)
   - [ ] 관계 다이어그램 (Mermaid classDiagram)
   - domain.md 규칙: 첫 Epic이 생성, 이후 Epic은 **업데이트** (덮어쓰기 금지)
   - concept.md = 풀 버전 템플릿, entity.md = 빠른 참조 스켈레톤

4. **Story 분해 + _epic.md 완성**
   - [ ] Use Case → Story 매핑 (Feature), 기술 작업 → Story (Enabler)
   - [ ] Story ID 부여 (US: User Story, TS: Technical Story)
   - [ ] Story당 예상 커밋 수 추정
   - [ ] _epic.md Stories 표 완성, 완료 조건 정의

5. **Execute**
   - [ ] `_epic.md`의 Stories 표에서 미완료(⏳ 또는 상태 없음) Story 목록 추출
   - [ ] 각 Story에 대해 순서대로 실행 (모든 Story 완료 전 다음 Step으로 넘어가지 말 것):
     ```
     Skill tool 호출: skill="writing-story"
       args: story_id={US|TS-NNN}, story_name={name}, epic_name={epic_name},
             goal_id={goal_id}, phase_id={phase_id}, project_path={project_path}
     → _story.md 생성 + 상태 ✅ 확인 후 다음 Story 진행
     ```
   - [ ] Story 완료 시 Epic 브랜치에 머지
   - [ ] 모든 Story 상태 ✅ 확인 후 Step 6으로 진행

6. **Wrap-up**
   - [ ] 모든 Story 상태 ✅ 확인 (미완료 있으면 Step 5로 돌아갈 것)
   - [ ] RETRO.md 작성 → ref: [assets/retro.md](assets/retro.md)
   - [ ] _epic.md 상태 → ✅
   - [ ] Skill tool 호출: `skill="workflow-pr"` → 부모 브랜치(Goal)로 PR 생성

## 폴더 구조

```
{goal_path}/
├── artifacts/                # 중간 산출물
│   ├── use-case/UC-NNN-{name}.md
│   └── concept/
│       ├── domain.md
│       └── entities/{entity}.md
└── epics/{epic_name}/
    ├── _epic.md
    ├── RETRO.md              # Wrap-up 시 생성
    └── stories/{US|TS}-NNN/
        └── _story.md
```

## Completion Checklist

- [ ] _epic.md 생성 완료
- [ ] Feature인 경우: Use Case 작성 완료
- [ ] Concept (domain.md, entities) 작성/업데이트 완료
- [ ] Story 분해 완료
- [ ] (Execute) 모든 Story에 writing-story invoke 완료
- [ ] (Wrap-up) RETRO.md 작성
- [ ] (Wrap-up) _epic.md 상태 ✅
- [ ] (Wrap-up) workflow-pr invoke 완료
