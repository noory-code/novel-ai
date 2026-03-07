---
name: execute-action-item
description: Implement one Action Item end-to-end: write the code, run tests, and commit — one focused change at a time.
metadata:
  version: "5.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [start an Action Item, execute Action Item, implement and commit, work on ACT-NNN, ACT-NNN]
  uses: []
---

# Writing Action Item

> An Action Item is the smallest workflow unit. 1 Action Item = 1 commit.

## Prerequisites

- `_story.md` exists; if not, invoke writing-story
- The corresponding ACT must be assigned in the Action Items table of _story.md
- All prerequisite ACTs listed in depends_on must be ✅ complete

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
| **story_id** | Y | Parent Story ID | US-001 |
| **story_name** | Y | Parent Story name | login-form |
| **action_item_id** | Y | Action Item ID | ACT-001 |
| **action_item_name** | Y | Action Item name | setup-project |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| Execute | Code/document changes | Files declared in output_paths | Final |
| Wrap-up | git commit | `[epic-name][story_id][ACT-NNN] title` | Final |
| Wrap-up | ACT status ✅ | Status update within `action-items/ACT-NNN-{name}.md` | Final |

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| Development skills (frontend-*, dev-*, design-*, etc.) | Actual coding and documentation work | Execute |

> Development skill selection: match task content keywords with skill-orchestration triggers

## Procedure

1. **Setup**
   - [ ] Confirm `_story.md` exists; if not, invoke writing-story
   - [ ] Confirm all prerequisite ACTs in depends_on are complete
   - [ ] Read the Action Item file — ref: [assets/action-item.md](assets/action-item.md)
   - [ ] Confirm the objective and task checklist
   - [ ] Check for previous ACT retrospectives: `Glob action-items/ACT-*.md` — if any completed ACTs exist, read their `## Retrospective` section and apply any "AI Improvements" noted there
   - [ ] Status → 🔄

2. **Write tests** (if code changes are required)
   - [ ] Design test cases based on acceptance criteria
   - [ ] Write Unit/Widget test code (Red — will fail since implementation is not yet done)

3. **Development**
   - [ ] Match task keywords to a development skill and invoke it
   - [ ] Perform the actual coding or documentation work
   - [ ] Complete all items in the task checklist

4. **Test verification**
   - [ ] Build passes
   - [ ] Tests pass (Green)
   - [ ] Confirm all files listed in output_paths exist

5. **Wrap-up**
   - [ ] Record the list of changed files in the Action Item file's results section
   - [ ] Commit (1 Action Item = 1 commit, following the message format)
   - [ ] Write `## Retrospective` section in the Action Item file — ref: [assets/retro.md](assets/retro.md)
     - Did well / Did poorly / Improvements / Instruction issues
   - [ ] Status → ✅
   - [ ] Decide the next Action Item or process Story completion

## Folder Structure

```
{epic_path}/stories/{story_id}/action-items/
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
| _story.md 누락 | `_story.md` 파일 없음 | `write-story` 스킬 호출 | Story 생성 후 이 스킬 재개 |
| Action Item 미할당 | _story.md Action Items 테이블에 ACT 정보 없음 | 오류 메시지 출력, _story.md 업데이트 요청 | 스킬 중단, 수동 수정 후 재개 |
| 의존성 미완료 | depends_on의 선행 ACT 상태가 ✅ 아님 | 미완료 ACT 목록 출력, 선행 작업 완료 요청 | 스킬 중단, 선행 작업 완료 후 재개 |
| Action Item 파일 누락 | `action-items/ACT-NNN-{name}.md` 없음 | 템플릿 참조하여 파일 생성 | 파일 생성 후 계속 진행 |
| 빌드 실패 | Step 4에서 빌드 커맨드 실패 | 빌드 오류 출력, 코드 수정 요청 | Test verification 단계 중단, 수정 후 재실행 |
| 테스트 실패 | Step 4에서 테스트 실패 | 실패한 테스트 목록 출력, 코드 수정 요청 | Test verification 단계 중단, 수정 후 재실행 |
| output_paths 파일 누락 | 선언된 파일이 실제로 생성되지 않음 | 누락 파일 목록 출력, 파일 생성 요청 | Test verification 단계 중단, 파일 생성 후 재실행 |
| 커밋 실패 | git commit 오류 (pre-commit hook 실패 등) | git 오류 메시지 출력, 수동 해결 요청 | Wrap-up 중단, 해결 후 커밋 재시도 |
| 개발 스킬 매칭 실패 | 키워드로 적절한 개발 스킬을 찾을 수 없음 | 사용자에게 수동 구현 요청 또는 스킬 추천 요청 | Development 단계 중단, 수동 작업 또는 스킬 지정 후 재개 |

## Completion Checklist

- [ ] Action Item objective achieved
- [ ] Task checklist complete
- [ ] Results (changed files, commit) recorded
- [ ] 1 Action Item = 1 commit principle observed
- [ ] (Wrap-up) Retrospective written in Action Item file
- [ ] (Wrap-up) Status ✅
- [ ] (Wrap-up) Next Action Item or Story completion confirmed
