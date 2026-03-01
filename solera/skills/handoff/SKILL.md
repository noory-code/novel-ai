---
name: handoff
description: 세션 간 컨텍스트 전달 - HANDOFF.md 업데이트
metadata:
  version: "1.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [handoff, 세션 종료, 컨텍스트 저장, 작업 인계]
  uses: [workflow-manage]
---

# Handoff

> 세션 간 컨텍스트 전달을 위한 HANDOFF.md 생성/업데이트

## 입력

없음 (현재 세션 상태 자동 감지)

## 산출물

| 파일 | 위치 | 용도 |
|------|------|------|
| HANDOFF.md | 프로젝트 루트 | 세션 간 컨텍스트 전달 (임시 상태) |

## 절차

### Step 1: 현재 세션 작업 파악

다음 정보를 수집하여 현재 세션의 작업을 파악한다:

1. **Git 상태 확인**:
   ```bash
   git status --short
   git diff --stat
   git log --oneline -5
   ```

2. **Todo 목록 확인**: 현재 세션의 todo list 상태

3. **progress.md 읽기**: [workflow-manage](../workflow-manage/SKILL.md) 스킬을 통해 현재 Phase/Goal/Epic/Story 확인

### Step 2: HANDOFF.md 읽기

1. `HANDOFF.md` 파일 읽기 시도
2. 파일이 없으면 [assets/handoff-template.md](assets/handoff-template.md)를 참조하여 신규 생성

### Step 3: 섹션 업데이트

Step 1에서 수집한 정보를 바탕으로 다음 섹션을 업데이트한다:

| 섹션 | 내용 | 출처 |
|------|------|------|
| **현재 작업** | 진행 중인 작업 1-2줄 요약 | progress.md + todo list |
| **완료 항목** | 이번 세션에서 완료한 작업 목록 | git diff + todo (completed) |
| **다음 단계** | 다음 세션에서 해야 할 작업 | todo (pending) + 사용자 입력 |
| **중요 결정사항** | 주요 의사결정 및 이유 | git log + 사용자 입력 |
| **참고 파일** | 변경된 주요 파일 경로 | git diff --name-only |
| **주의사항** | 다음 세션에서 알아야 할 특이사항 | 사용자 입력 |

### Step 4: 타임스탬프와 함께 저장

1. 파일 상단에 `> 마지막 업데이트: YYYY-MM-DD HH:MM:SS` 추가
2. HANDOFF.md 저장

## 에러 처리

| 실패 지점 | 조건 | 복구 절차 |
|-----------|------|----------|
| HANDOFF.md 읽기 실패 | 파일 미존재 | 프로젝트 루트에 신규 생성 (템플릿 참조) |
| 현재 작업 파악 불가 | git diff/log 비어 있음 | 사용자에게 "이번 세션에서 한 작업을 알려주세요" 질문 |
| HANDOFF.md 쓰기 실패 | 권한 에러 | `chmod 644 HANDOFF.md` 실행 후 재시도 |

## 사용 시점

- 작업 중단 전
- 컨텍스트 윈도우 한계 도달 전
- 복잡한 작업 중간 저장

## progress.md vs HANDOFF.md

> 두 파일의 차이점은 [assets/handoff-template.md](assets/handoff-template.md) 참조

## References

| 파일 | 내용 |
|------|------|
| [assets/handoff-template.md](assets/handoff-template.md) | HANDOFF.md 형식 + progress.md와의 차이점 |
| [assets/self-verification.md](assets/self-verification.md) | 스킬 자동 검증 TC |

## Completion Checklist

- [ ] git status/diff/log로 현재 작업 파악했는가?
- [ ] progress.md에서 현재 Phase/Goal/Epic 확인했는가?
- [ ] HANDOFF.md를 읽거나 생성했는가?
- [ ] 6개 섹션(현재 작업, 완료 항목, 다음 단계, 결정사항, 참고 파일, 주의사항)을 업데이트했는가?
- [ ] 타임스탬프를 추가했는가?
- [ ] HANDOFF.md를 저장했는가?
