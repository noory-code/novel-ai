---
name: manage-workflow
description: Know what to work on next — track progress, pick up where you left off, or close out a completed item.
metadata:
  version: "5.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [what should I work on, mark work complete, show current progress, update progress, write a retrospective, next task]
  uses: [write-identity, write-phase, write-goal, write-epic, write-story, execute-action-item, transition-catalog]
---

# Workflow Manage (Supervisor)

> The workflow manager **reads and executes — it does not define**.
> The `## Workflow` section of each work item template is the SSOT.

## Common Rules

- [conventions.md](assets/conventions.md) (hierarchy, Git branches, folder structure, status values)
- [lifecycle.md](assets/lifecycle.md) (Workflow pattern description)

## Prerequisites

- `[project]/progress.md` exists; if not, initialize it (ref: [assets/progress.md](assets/progress.md))

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **action** | N | Action type | start \| complete \| check \| next |
| **work_item** | N | Target work item path | _goal.md, _epic.md, _story.md |

## Output

| Action | Output | Path |
|--------|--------|------|
| start / complete | progress.md update | `{project}/progress.md` |
| complete (Epic/Goal) | RETRO.md written | `{path}/RETRO.md` |
| next | Next work item decided | — |

## Procedure

### start — Start work item

1. Read the target work item (_goal.md | _epic.md | _story.md)
2. Extract the `## Workflow` section
3. Execute each step of the Workflow in order
4. If document writing is required, invoke writing-* skills
5. Update progress.md

### complete — Complete work item

1. Read the target work item
2. Execute the latter steps of `## Workflow` (completion check, status change, etc.)
3. If the item is an Epic or Goal, write RETRO.md
4. Update progress.md
5. Decide the next work item

### check — Check current status

1. Read progress.md
2. Return the current Phase, Goal, Epic, and Story

### next — Decide next work

1. Story complete and Epic has remaining Stories → start the next Story
2. Epic complete and Goal has remaining Epics → write an Epic retrospective, then start the next Epic
3. Goal complete → write a Goal retrospective, then invoke catalog-transition
4. Otherwise → continue current work

## Responsibilities

| Role | Skill |
|------|-------|
| **Document writing** | writing-identity, writing-phase, writing-goal, writing-epic, writing-story, writing-action-item |
| **Execution supervision** | workflow-manage |
| **Completion handling** | catalog-transition |

## Supervision Principles

- Reads the work item's `## Workflow` as the SSOT
- Does not define procedures directly — follows procedures defined in the template
- Delegates document writing to writing-* skills
- Delegates development work to frontend-*, dev-* skills

## Templates

- [assets/progress.md](assets/progress.md)
- [assets/retro.md](assets/retro.md)
- [assets/status.md](assets/status.md)

## References

### Verification

| File | Content |
|------|---------|
| [self-verification.md](assets/self-verification.md) | Automated skill definition verification TCs (9 cases) |

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| progress.md 없음 | `{project}/progress.md` 파일 없음 | [assets/progress.md](assets/progress.md) 템플릿으로 초기화 | 파일 생성 후 계속 진행 |
| work_item 파일 없음 | 지정된 _goal.md/_epic.md/_story.md 없음 | 오류 메시지 출력, 파일 경로 확인 요청 | 스킬 중단, 올바른 경로 입력 후 재개 |
| Workflow 섹션 없음 | work item에 `## Workflow` 섹션 없음 | 기본 workflow 패턴 적용 (lifecycle.md 참조) | 계속 진행 (기본 패턴 사용) |
| writing-* 스킬 호출 실패 | 하위 스킬 호출 오류 | 실패한 스킬 이름 출력, 수동 실행 요청 | 해당 단계 중단, 수동 처리 후 재개 |
| 상태 불일치 | Story ✅인데 Epic이 🔄 | 불일치 항목 출력, 상태 동기화 요청 | 다음 작업 결정 전 중단, 수동 동기화 후 재개 |
| 다음 작업 없음 | 모든 작업 완료, next 호출 시 | "모든 작업 완료" 메시지 출력 | 스킬 정상 완료 |
| RETRO.md 작성 실패 | Epic/Goal 완료 시 회고 작성 오류 | 템플릿 경로 확인, 수동 작성 요청 | complete 단계 중단, 수동 작성 후 재개 |
| progress.md 업데이트 실패 | 파일 쓰기 권한 오류 | 권한 확인, `chmod 644 progress.md` 안내 | 스킬 중단, 권한 수정 후 재시도 |

## Completion Checklist

- [ ] Read the Workflow section of the work item?
- [ ] Executed Workflow steps in order?
- [ ] Updated progress.md?
- [ ] Wrote a retrospective upon completion? (Epic/Goal)
- [ ] Decided the next work item?
