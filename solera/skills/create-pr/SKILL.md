---
name: create-pr
description: Wrap up an Epic by opening a PR, reviewing the diff, and merging cleanly into the parent branch.
metadata:
  version: "3.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [create a pull request, open a PR, merge the Epic, merge into parent branch, submit for review]
  uses: []
---

# Workflow PR

> Upon Epic completion, creates a PR to the parent branch, reviews it, and merges.

## Prerequisites

- All Stories in the Epic have been squash merged (status ✅)
- Build and tests pass on the Epic branch

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **epic_branch** | Y | PR source branch | epic-auth |
| **target_branch** | Y | Merge target branch | dev, main |

## Output

| Step | Output | Description |
|------|--------|-------------|
| Create PR | GitHub PR (URL) | One PR per Epic |
| Merge | Merge commit | squash merge |

## Procedure

1. **Prepare PR**
   - [ ] Confirm all Stories in the Epic are ✅
   - [ ] Confirm build and tests pass
   - [ ] Confirm no conflicts against target_branch (rebase if conflicts exist)

2. **Create PR**
   - [ ] `gh pr create --base {target_branch} --head {epic_branch}`
   - [ ] PR title: `[Epic] {epic_name}: {one-line summary}`
   - [ ] PR body: Stories list, key changes, test results — ref: [assets/pr-template.md](assets/pr-template.md)

3. **Handle review**
   - [ ] Check review comments
   - [ ] Add commits to the Epic branch for any fixes
   - [ ] Re-confirm CI passes

4. **Merge**
   - [ ] Execute the PR squash merge
   - [ ] Confirm the source branch is deleted

## PR Title Format

```
[Epic] {epic-name}: {summary}
```

## References

| File | Content |
|------|---------|
| [assets/pr-template.md](assets/pr-template.md) | PR body template |
| [self-verification.md](assets/self-verification.md) | Automated skill definition verification TCs (7 cases) |

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| Stories 미완료 | Epic의 일부 Story 상태가 ✅ 아님 | 미완료 Story 목록 출력, 완료 요청 | 스킬 중단, 모든 Story 완료 후 재개 |
| 빌드/테스트 실패 | Epic 브랜치에서 빌드 또는 테스트 실패 | 오류 출력, 수정 요청 | 스킬 중단, 수정 후 재개 |
| 브랜치 충돌 | target_branch와 충돌 발생 | 충돌 파일 목록 출력, rebase 후 재시도 요청 | Prepare 단계 중단, rebase 후 재개 |
| gh CLI 미설치 | `gh` 명령어 없음 | GitHub CLI 설치 안내 출력 | 스킬 중단, 설치 후 재개 |
| PR 생성 실패 | gh pr create 오류 (권한, 인증 등) | gh 오류 메시지 출력, 인증 확인 요청 | Create PR 단계 중단, 인증 후 재시도 |
| CI 실패 | PR의 CI 체크 실패 | 실패한 CI 작업 출력, 수정 요청 | Handle review 단계 중단, 수정 커밋 추가 후 재확인 |
| Merge 실패 | squash merge 오류 | 오류 메시지 출력, 수동 merge 요청 | Merge 단계 중단, 수동 처리 후 확인 |
| 브랜치 삭제 실패 | 소스 브랜치 삭제 실패 | 경고 메시지 출력, 수동 삭제 요청 | 스킬 완료 (삭제는 필수 아님), 수동 정리 권장 |

## Completion Checklist

- [ ] PR created
- [ ] CI passed
- [ ] Review complete
- [ ] Merge complete
- [ ] Source branch deleted
