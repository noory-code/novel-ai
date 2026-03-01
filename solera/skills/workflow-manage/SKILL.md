---
name: workflow-manage
description: 워크플로우 감독자. 일감의 Workflow를 읽고 실행한다.
metadata:
  version: "4.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [작업 시작, 작업 완료, 현재 작업, 다음 작업, progress 업데이트, 회고 작성]
  uses: [writing-phase, writing-goal, writing-epic, writing-story, writing-action-item, catalog-transition]
---

# Workflow Manage (감독자)

> 워크플로우 매니저는 **정의하지 않고 읽고 실행**한다.
> 각 일감 템플릿의 `## Workflow` 섹션이 SSOT이다.

## 공통 규칙

- [conventions.md](assets/conventions.md) (계층, Git 브랜치, 폴더 구조, 상태값)
- [lifecycle.md](assets/lifecycle.md) (Workflow 패턴 설명)

## 선행조건

- `[project]/progress.md` 존재 → 없으면 초기화 (ref: [assets/progress.md](assets/progress.md))

## 입력

| 파라미터 | 필수 | 설명 | 예시 |
|----------|------|------|------|
| **action** | N | 동작 유형 | start \| complete \| check \| next |
| **work_item** | N | 대상 일감 경로 | _goal.md, _epic.md, _story.md |

## 산출물

| 동작 | 산출물 | 경로 |
|------|--------|------|
| start / complete | progress.md 갱신 | `{project}/progress.md` |
| complete (Epic/Goal) | RETRO.md 작성 | `{path}/RETRO.md` |
| next | 다음 일감 결정 | — |

## 절차

### start — 일감 시작

1. 대상 일감 읽기 (_goal.md | _epic.md | _story.md)
2. `## Workflow` 섹션 추출
3. Workflow의 각 단계를 순서대로 실행
4. 문서 작성이 필요하면 writing-* 스킬 invoke
5. progress.md 업데이트

### complete — 일감 완료

1. 대상 일감 읽기
2. `## Workflow` 후반 단계 실행 (완료 확인, 상태 변경 등)
3. Epic/Goal이면 RETRO.md 작성
4. progress.md 업데이트
5. 다음 작업 결정

### check — 현재 상태 확인

1. progress.md 읽기
2. 현재 Phase, Goal, Epic, Story 반환

### next — 다음 작업 결정

1. Story 완료 + Epic에 남은 Story 있음 → 다음 Story start
2. Epic 완료 + Goal에 남은 Epic 있음 → Epic 회고 → 다음 Epic start
3. Goal 완료 → Goal 회고 → catalog-transition invoke
4. 그 외 → 현재 작업 계속

## 역할 분담

| 역할 | 스킬 |
|------|------|
| **문서 작성** | writing-identity, writing-phase, writing-goal, writing-epic, writing-story, writing-action-item |
| **실행 감독** | workflow-manage (이 스킬) |
| **완료 처리** | catalog-transition |

## 감독 원칙

- 일감의 `## Workflow`를 SSOT로 읽는다
- 직접 절차를 정의하지 않는다 — 템플릿에 정의된 절차를 따른다
- 문서 작성이 필요하면 writing-* 스킬에 위임한다
- 개발 작업이 필요하면 frontend-*, dev-* 스킬에 위임한다

## 템플릿

- [assets/progress.md](assets/progress.md)
- [assets/retro.md](assets/retro.md)
- [assets/status.md](assets/status.md)

## References

### 검증

| 파일 | 내용 |
|------|------|
| [self-verification.md](assets/self-verification.md) | 스킬 정의 자동 검증 TC (9건) |

## Completion Checklist

- [ ] 일감의 Workflow 섹션을 읽었는가?
- [ ] Workflow 단계를 순서대로 실행했는가?
- [ ] progress.md 업데이트했는가?
- [ ] 완료 시 회고를 작성했는가? (Epic/Goal)
- [ ] 다음 작업을 결정했는가?
