---
name: write-phase
description: Plan a quarter — distribute Goals across a Phase and track which ones are in progress or complete.
metadata:
  version: "3.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [define a Phase, start a Phase, plan the quarter, set up quarterly goals, write Phase README]
  uses: [write-goal]
---

# Writing Phase

> Writes the Phase README.md and tracks Goal execution.

## Prerequisites

- `workspace/initiative/[year]/roadmap.md` exists; if not, request it from the user

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **project_path** | Y | Project workspace root | banas/workspace |
| **year** | Y | Initiative year | 2026 |
| **phase_id** | Y | Phase ID | 2026-P1-foundation |

## Output

| Step | Output | Path |
|------|--------|------|
| Create | Phase README | `{project_path}/phase/{phase_id}/README.md` |
| Create | Goal folder structure | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/` |
| Wrap-up | Phase summary | `{project_path}/phase/{phase_id}/SUMMARY.md` |
| Wrap-up | Phase retrospective | `{project_path}/phase/{phase_id}/RETRO.md` |
| Wrap-up | progress.md update | `{project_path}/progress.md` |

## Skills Used

| Skill | Purpose | Step |
|-------|---------|------|
| `write-goal` | Elaborate each Goal and decompose it into Epics | Execute |
| `transition-catalog` | Promote artifacts incrementally (at Goal Create and Epic Wrap-up) | Execute (within Goal/Epic) |

## Procedure

1. **Verify roadmap**
   - [ ] Read `{project_path}/initiative/{year}/roadmap.md`
   - [ ] Extract the Goals list for this Phase from the Phase planning table
   - [ ] If no Goals are found, confirm with the user

2. **Create Phase folder**
   - [ ] Create `{project_path}/phase/{phase_id}/`
   - [ ] Create `{project_path}/phase/{phase_id}/goals/`

3. **Write README.md** — ref: [assets/phase-template.md](assets/phase-template.md)
   - [ ] Overview table (period, objectives)
   - [ ] Goals table (Goals extracted from roadmap)
   - [ ] Completion criteria (key criteria for each Goal)
   - [ ] Workflow section (template as-is)

4. **Create Goal folder structure**
   - [ ] Create `goals/{goal_id}-{name}/` for each Goal
   - [ ] Prepare to invoke write-goal

5. **Phase Wrap-up**
   - [ ] Confirm all Goal statuses ✅
   - [ ] Confirm artifacts/ is empty for each Goal (promoted incrementally during Goal Create and Epic Wrap-ups)
   - [ ] Write SUMMARY.md (overall Goal outcomes, catalog artifact list, handoff notes for the next Phase)
   - [ ] Write RETRO.md — ref: [assets/retro.md](assets/retro.md)
   - [ ] Set README.md status to ✅ and update progress
   - [ ] Update progress.md

## Folder Structure

```
{project_path}/phase/{phase_id}/
├── README.md
├── SUMMARY.md      # Created at Wrap-up (see phase-template.md Step 3)
├── RETRO.md        # Created at Wrap-up
└── goals/
    ├── {goal_id}-{name}/
    │   ├── _goal.md
    │   ├── artifacts/    # Promoted incrementally at Goal Create and Epic Wrap-up
    │   └── epics/
    └── ...
```

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| roadmap.md 누락 | `initiative/{year}/roadmap.md` 파일이 없음 | 사용자에게 roadmap.md 제공 요청 | 파일 제공될 때까지 스킬 중단 |
| Goals 목록 없음 | roadmap.md에서 Phase 계획을 찾을 수 없음 | 사용자에게 확인 요청 | 사용자 확인 후 계속 진행 또는 중단 |
| phase_id 형식 오류 | phase_id가 규칙에 맞지 않음 (예: YYYY-PX-name) | 올바른 형식 예시와 함께 오류 메시지 출력 | 스킬 중단, 올바른 phase_id 입력 요청 |
| 폴더 생성 실패 | 권한 오류 또는 경로 문제 | 오류 메시지 출력, 권한 확인 요청 | 스킬 중단, 오류 상태 반환 |
| write-goal 실패 | 하위 스킬 호출 실패 | 실패한 Goal 기록, 사용자에게 알림 | 해당 Goal 건너뛰고 계속 진행 또는 중단 |
| artifacts/ 비어있지 않음 | Goal의 artifacts가 완전히 승격되지 않음 | 남은 파일 목록 출력, 수동 확인 요청 | 경고 출력 후 계속 진행 |

## Completion Checklist

- [ ] README.md created
- [ ] Goals table includes all Goals from the roadmap
- [ ] Folder structure created for each Goal
- [ ] write-goal invoked for all Goals
- [ ] (Wrap-up) All Goal artifacts/ directories are empty
- [ ] (Wrap-up) SUMMARY.md written
- [ ] (Wrap-up) RETRO.md written
- [ ] (Wrap-up) progress.md updated
