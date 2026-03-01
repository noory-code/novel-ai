---
name: writing-action-item
description: Action Item 실행. 1 Action Item = 1 커밋.
metadata:
  version: "4.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [Action Item 시작, Action Item 실행, 커밋 작업, ACT-NNN]
  uses: []
---

# Writing Action Item

> Action Item은 가장 작은 워크플로우 단위이다. 1 Action Item = 1 커밋.

## 선행조건

- `_story.md` 존재 → 없으면 writing-story invoke
- _story.md의 Action Items 표에 해당 ACT가 배정되어 있을 것
- depends_on에 명시된 선행 ACT가 모두 ✅ 완료일 것

## 입력

| 파라미터 | 필수 | 설명 | 예시 |
|----------|------|------|------|
| **epic_name** | Y | 소속 Epic 이름 | 01-auth |
| **story_id** | Y | 소속 Story ID | US-001 |
| **action_item_id** | Y | Action Item ID | ACT-001 |
| **action_item_name** | Y | Action Item 이름 | setup-project |

## 산출물

| Step | 산출물 | 경로 |
|------|--------|------|
| Execute | 코드/문서 변경 | output_paths에 선언된 파일들 |
| Wrap-up | git commit | `[epic-name][story_id][ACT-NNN] 제목` |
| Wrap-up | ACT 상태 ✅ | `action-items/ACT-NNN-{name}.md` 내 상태 갱신 |

## 사용 스킬

| 스킬 | 용도 | Step |
|------|------|------|
| 개발 스킬 (frontend-*, dev-*, design-* 등) | 실제 코딩/문서 작업 | Execute |

> 개발 스킬 선택: 작업 내용 키워드를 skill-orchestration 트리거와 매칭

## 절차

1. **Setup**
   - [ ] `_story.md` 존재 확인 → 없으면 writing-story invoke
   - [ ] depends_on 선행 ACT 완료 확인
   - [ ] Action Item 파일 읽기 → ref: [assets/action-item.md](assets/action-item.md)
   - [ ] 목표 + 작업 내용 체크리스트 확인
   - [ ] 상태 → 🔄

2. **테스트 작성** (코드 변경 시)
   - [ ] 인수 조건 기반 테스트 케이스 설계
   - [ ] Unit/Widget 테스트 코드 작성 (Red — 아직 구현 없으므로 실패)

3. **개발**
   - [ ] 작업 키워드 → 개발 스킬 매칭 → invoke
   - [ ] 실제 코딩/문서 작업 수행
   - [ ] 작업 내용 체크리스트 전부 완료

4. **테스트 검증**
   - [ ] 빌드 통과
   - [ ] 테스트 통과 (Green)
   - [ ] output_paths 파일 존재 확인

5. **Wrap-up**
   - [ ] 변경 파일 목록 기록 (Action Item 파일 결과 섹션)
   - [ ] 커밋 (1 Action Item = 1 커밋, 메시지 형식 준수)
   - [ ] 상태 → ✅
   - [ ] 다음 Action Item 결정 또는 Story 완료 처리

## 폴더 구조

```
{epic_path}/stories/{story_id}/action-items/
└── ACT-NNN-{name}.md
```

## 커밋 메시지 형식

```
[epic-name][US-NNN][ACT-NNN] 제목

- 변경 내용
```

## Completion Checklist

- [ ] Action Item 목표 달성
- [ ] 작업 내용 체크리스트 완료
- [ ] 결과 (변경 파일, 커밋) 기록
- [ ] 1 Action Item = 1 커밋 원칙 준수
- [ ] (Wrap-up) 상태 ✅
- [ ] (Wrap-up) 다음 Action Item 또는 Story 완료 확인
