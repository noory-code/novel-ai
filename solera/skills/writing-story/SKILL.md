---
name: writing-story
description: Story 문서 작성 → Action Item 분해. 1 Action Item = 1 커밋.
metadata:
  version: "5.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [Story 상세화, Story 시작, Action Item으로 분해, 커밋 단위]
  uses: [writing-action-item]
---

# Writing Story

> _story.md를 작성하고, Action Item으로 분해한다.

## 선행조건

- `published/identity/mission.md` 존재
  - 없으면: Glob tool로 `published/identity/mission.md` 확인 → Skill tool로 `writing-identity` invoke
- `_epic.md` 존재
  - 없으면: Glob tool로 `{epic_path}/_epic.md` 확인 → Skill tool로 `writing-epic` invoke
- _epic.md의 Stories 표에 해당 Story가 배정되어 있을 것

## 입력

| 파라미터 | 필수 | 설명 | 예시 |
|----------|------|------|------|
| **project_path** | Y | 프로젝트 workspace 루트 | banas/workspace |
| **phase_id** | Y | 소속 Phase ID | 2026-P1-foundation |
| **goal_id** | Y | 소속 Goal ID | G1-search-liquor |
| **epic_name** | Y | 소속 Epic 이름 | 01-auth |
| **story_id** | Y | Story ID | US-001 |
| **story_name** | Y | Story 이름 | login-form |
| **story_type** | N | US (User Story) \| TS (Technical Story) (기본: US) | TS |

## 산출물

| Step | 산출물 | 성격 | 경로 |
|------|--------|------|------|
| Create | _story.md | 최종 | `{epic_path}/stories/{story_id}/_story.md` |
| Create | ACT-NNN-{name}.md | 최종 | `{epic_path}/stories/{story_id}/action-items/ACT-NNN-{name}.md` |
| Wrap-up | RETRO.md | 최종 | `{epic_path}/stories/{story_id}/RETRO.md` |

> `{epic_path}` = `{project_path}/phase/{phase_id}/goals/{goal_id}/epics/{epic_name}`

## 사용 스킬

| 스킬 | 용도 | Step |
|------|------|------|
| `writing-action-item` | 각 Action Item 실행 (1 ACT = 1 커밋) | Execute |
| `workflow-pr` | Story 완료 시 Epic 브랜치로 PR | Wrap-up |

## 절차

1. **Setup**
   - [ ] Glob tool로 `{epic_path}/_epic.md` 존재 확인
     - 없으면: Skill tool `skill="writing-epic"` invoke → 완료 후 이 Step 재개
   - [ ] `story-{story_id}-{story_name}` 브랜치 생성 (from Epic 브랜치)
   - [ ] `{epic_path}/stories/{story_id}/` 폴더 생성
   - [ ] 상태 → 🔄

2. **Story 유형 결정 + 인수 조건 정의**
   - [ ] US (User Story) vs TS (Technical Story) 결정
   - [ ] 검증 가능한 인수 조건 정의
   - [ ] 완료 정의 명확화

3. **_story.md 작성 + Action Item 분해**
   - [ ] _story.md 작성 → ref: [assets/story.md](assets/story.md)
     - US: As a / I want / So that
     - TS: 기술 목표 + 스펙
   - [ ] 인수 조건 포함
   - [ ] Action Items 표 작성
   - [ ] Action Item별 파일 생성 (`action-items/ACT-NNN-{name}.md`)
   - [ ] 1 Action Item = 1 커밋 원칙
   - [ ] Action Item별 Agent 배정 (에이전트 팀 사용 시)
   - [ ] depends_on 정의 → 산출물 충돌 방지
   - [ ] Phase 배분 (같은 Phase = 병렬 가능)

4. **Execute**
   - [ ] `_story.md`의 Action Items 표에서 미완료(⏳ 또는 상태 없음) Action Item 목록 추출
   - [ ] Phase 순서대로 각 Action Item 실행 (모든 Action Item 완료 전 다음 Step으로 넘어가지 말 것):
     ```
     Skill tool 호출: skill="writing-action-item"
       args: action_item_id=ACT-NNN, action_item_name={name}, story_id={story_id},
             epic_name={epic_name}, goal_id={goal_id}, phase_id={phase_id},
             project_path={project_path}
     → ACT-NNN.md 커밋 완료 + 상태 ✅ 확인 후 다음 Action Item 진행
     ```
   - [ ] 모든 인수 조건 충족 확인
   - [ ] 모든 Action Item 상태 ✅ 확인 후 Step 5로 진행

5. **Wrap-up**
   - [ ] 전체 테스트 통과 확인 (코드 변경 시)
   - [ ] RETRO.md 작성 → ref: [assets/retro.md](assets/retro.md)
   - [ ] _story.md 상태 → ✅
   - [ ] Epic 브랜치에 스쿼시 머지
   - [ ] Skill tool 호출: `skill="workflow-pr"` (Story → Epic 브랜치)

## 폴더 구조

```
{epic_path}/stories/{story_id}/
├── _story.md
├── RETRO.md              # Wrap-up 시 생성
└── action-items/
    └── ACT-NNN-{name}.md
```

## 커밋 메시지 형식

```
[epic-name][US-NNN][ACT-NNN] 제목

- 변경 내용
```

## Completion Checklist

- [ ] _story.md 작성 완료
- [ ] 인수 조건 검증 가능
- [ ] Action Item 파일 생성 완료
- [ ] 1 Action Item = 1 커밋 원칙 준수
- [ ] (Execute) 모든 Action Item에 writing-action-item invoke 완료
- [ ] (Wrap-up) RETRO.md 작성
- [ ] (Wrap-up) _story.md 상태 ✅
- [ ] (Wrap-up) Epic 브랜치에 스쿼시 머지
