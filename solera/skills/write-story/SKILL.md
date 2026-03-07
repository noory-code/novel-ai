---
name: write-story
description: Write a Story with clear acceptance criteria, then break it into atomic Action Items — each one a single commit.
metadata:
  version: "6.0.0"
  category: writing
  type: composite
  style: procedural
  execution_model: sequential
  triggers: [write a Story, plan a Story, start a Story, break Story into Action Items, define acceptance criteria]
  uses: [execute-action-item]
---

# Writing Story

> Writes _story.md and decomposes the Story into Action Items.

## Prerequisites

- `published/identity/mission.md` exists
  - If not: check `published/identity/mission.md` with Glob tool → invoke `writing-identity` with Skill tool
- `_epic.md` exists
  - If not: check `{epic_path}/_epic.md` with Glob tool → invoke `writing-epic` with Skill tool
- The corresponding Story must be assigned in the Stories table of _epic.md

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas/workspace |
| **year** | Y | Initiative year | 2026 |
| **phase_id** | Y | Parent Phase ID | 2026-P1-foundation |
| **goal_id** | Y | Parent Goal ID | G1 |
| **goal_name** | Y | Parent Goal name | search-liquor |
| **epic_name** | Y | Parent Epic name | 01-auth |
| **epic_type** | N | Feature \| Enabler (default: Feature) | Enabler |
| **story_id** | Y | Story ID | US-001 |
| **story_name** | Y | Story name | login-form |
| **story_type** | N | US (User Story) \| TS (Technical Story) (default: US) | TS |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Create | _story.md | `{epic_path}/stories/{story_id}/_story.md` | Final |
| Create | ACT-NNN-{name}.md | `{epic_path}/stories/{story_id}/action-items/ACT-NNN-{name}.md` | Final |
| Wrap-up | RETRO.md | `{epic_path}/stories/{story_id}/RETRO.md` | Final |

> `{epic_path}` = `{project_path}/phase/{phase_id}/goals/{goal_id}/epics/{epic_name}`

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `writing-action-item` | Execute each Action Item (1 ACT = 1 commit) | Execute |

## Procedure

1. **Setup**
   - [ ] Confirm `{epic_path}/_epic.md` exists with Glob tool
     - If not: invoke Skill tool `skill="writing-epic"` **(BLOCKING: Epic 생성 완료 후 재개)**
   - [ ] Check for previous Story retrospectives: `Glob {epic_path}/stories/*/RETRO.md` — if any exist, read the most recent one and apply any "AI Improvements" noted there
   - [ ] Create `story-{story_id}-{story_name}` branch (from Epic branch)
   - [ ] Create `{epic_path}/stories/{story_id}/` folder
   - [ ] Status → 🔄

2. **Determine Story type and define acceptance criteria**
   - [ ] Decide US (User Story) vs TS (Technical Story)
   - [ ] Define verifiable acceptance criteria
   - [ ] Clarify the definition of done

3. **Write _story.md and decompose Action Items**
   - [ ] Write _story.md — ref: [assets/story.md](assets/story.md)
     - US: As a / I want / So that
     - TS: Technical objective + spec
   - [ ] Include acceptance criteria
   - [ ] Write the Action Items table (apply 1 Action Item = 1 commit principle)
   - [ ] Assign an Agent for each Action Item (when using agent teams)
   - [ ] Define depends_on to prevent output conflicts
   - [ ] Distribute across phases (same phase = can run in parallel)
   - [ ] **MUST: Immediately after writing _story.md, create one file per Action Item.**
     - Parse every row in the Action Items table
     - For each row: create `action-items/ACT-NNN-{name}.md` using the template in [assets/action-item.md](../execute-action-item/assets/action-item.md)
     - Do NOT proceed to Step 4 until all files exist
   - [ ] Verify all Action Item files exist: `Glob action-items/ACT-*.md` — count must match the table row count

4. **Execute**
   - [ ] Extract incomplete (⏳ or no status) Action Items from the Action Items table in `_story.md`
   - [ ] Execute each Action Item in phase order **(BLOCKING: 각 Action Item이 완료될 때까지 대기, 순차적으로 실행)**:
     ```
     Skill tool call: skill="writing-action-item"
       args: project_path={project_path}, year={year}, phase_id={phase_id},
             goal_id={goal_id}, goal_name={goal_name}, epic_name={epic_name},
             epic_type={epic_type}, story_id={story_id}, story_name={story_name},
             action_item_id=ACT-NNN, action_item_name={name}
     → Confirm ACT-NNN.md committed + status ✅ before proceeding to next Action Item
     ```
   - [ ] Confirm all acceptance criteria are met
   - [ ] Proceed to Step 5 after confirming all Action Item statuses ✅

5. **Wrap-up**
   - [ ] Confirm all tests pass (if code changes were made)
   - [ ] Write RETRO.md — ref: [assets/retro.md](assets/retro.md)
   - [ ] Set _story.md status to ✅
   - [ ] Squash merge to the Epic branch

## Folder Structure

```
{epic_path}/stories/{story_id}/
├── _story.md
├── RETRO.md              # Created at Wrap-up
└── action-items/
    └── ACT-NNN-{name}.md
```

## Commit Message Format

```
[epic-name][US-NNN][ACT-NNN] title

- change description
```

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| mission.md 누락 | `published/identity/mission.md` 없음 | Glob으로 확인 후 Skill tool로 `write-identity` 호출 | identity 생성 후 이 스킬 재개 |
| _epic.md 누락 | `{epic_path}/_epic.md` 없음 | Glob으로 확인 후 Skill tool로 `write-epic` 호출 | Epic 생성 후 이 스킬 재개 |
| Story 미할당 | _epic.md Stories 테이블에 Story 정보 없음 | 오류 메시지 출력, _epic.md 업데이트 요청 | 스킬 중단, 수동 수정 후 재개 |
| 브랜치 생성 실패 | git 오류 (충돌, 권한 등) | git 오류 메시지 출력, 수동 해결 요청 | 스킬 중단, 해결 후 재개 |
| Action Item 파일 미생성 | Step 3에서 파일 생성 누락 | Glob으로 확인, 누락된 파일 목록 출력 후 재생성 | 모든 파일 생성 확인될 때까지 Step 4 진입 차단 |
| Action Item 개수 불일치 | 테이블 행 수와 파일 수 불일치 | 차이 출력, 테이블 또는 파일 수정 요청 | Step 4 진입 차단, 수동 수정 후 재개 |
| 의존성 순환 참조 | depends_on에 순환 구조 존재 | 순환 의존성 경로 출력, 테이블 수정 요청 | Execute 단계 중단, 수동 수정 후 재개 |
| execute-action-item 실패 | 하위 스킬 호출 실패 | 실패한 Action Item 기록, 사용자에게 알림 | 해당 Action Item 건너뛰고 계속 진행 또는 중단 |
| Squash merge 실패 | git 충돌 또는 권한 오류 | 충돌 파일 목록 출력, 수동 해결 요청 | Wrap-up 중단, 수동 해결 후 재개 |

## Completion Checklist

- [ ] _story.md written
- [ ] Acceptance criteria are verifiable
- [ ] All ACT-NNN-{name}.md files exist on disk (verified with Glob tool — count matches Action Items table)
- [ ] 1 Action Item = 1 commit principle observed
- [ ] (Execute) writing-action-item invoked for all Action Items
- [ ] (Wrap-up) RETRO.md written
- [ ] (Wrap-up) _story.md status ✅
- [ ] (Wrap-up) Squash merged to Epic branch
