---
name: workflow-pr
description: Epic 완료 시 부모 브랜치로 PR 생성 → 리뷰 → 머지.
metadata:
  version: "2.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [PR 생성, PR 만들어줘, Epic 머지, 부모 브랜치로 머지]
  uses: []
---

# Workflow PR

> Epic 완료 시 부모 브랜치로 PR을 생성하고, 리뷰 후 머지한다.

## 선행조건

- Epic의 모든 Story 스쿼시 머지 완료 (상태 ✅)
- Epic 브랜치에서 빌드/테스트 통과

## 입력

| 파라미터 | 필수 | 설명 | 예시 |
|----------|------|------|------|
| **epic_branch** | Y | PR 소스 브랜치 | epic-auth |
| **target_branch** | Y | 머지 대상 브랜치 | dev, main |

## 산출물

| Step | 산출물 | 설명 |
|------|--------|------|
| PR 생성 | GitHub PR (URL) | Epic 단위 PR |
| 머지 | 머지 커밋 | squash merge |

## 절차

1. **PR 준비**
   - [ ] Epic의 모든 Story ✅ 확인
   - [ ] 빌드/테스트 통과 확인
   - [ ] target_branch 대비 충돌 없음 확인 (충돌 시 rebase)

2. **PR 생성**
   - [ ] `gh pr create --base {target_branch} --head {epic_branch}`
   - [ ] PR 제목: `[Epic] {epic_name}: {1줄 요약}`
   - [ ] PR 본문: Stories 목록, 주요 변경사항, 테스트 결과 → ref: [assets/pr-template.md](assets/pr-template.md)

3. **리뷰 대응**
   - [ ] 리뷰 코멘트 확인
   - [ ] 수정 시 Epic 브랜치에서 추가 커밋
   - [ ] CI 통과 재확인

4. **머지**
   - [ ] PR squash merge 실행
   - [ ] 소스 브랜치 삭제 확인

## PR 제목 형식

```
[Epic] {epic-name}: {요약}
```

## References

| 파일 | 내용 |
|------|------|
| [assets/pr-template.md](assets/pr-template.md) | PR 본문 템플릿 |
| [self-verification.md](assets/self-verification.md) | 스킬 정의 자동 검증 TC (7건) |

## Completion Checklist

- [ ] PR 생성 완료
- [ ] CI 통과
- [ ] 리뷰 완료
- [ ] 머지 완료
- [ ] 소스 브랜치 삭제
