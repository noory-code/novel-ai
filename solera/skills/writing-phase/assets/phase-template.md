# Template: Phase README.md

## README.md

```markdown
# Phase: [phase-id]

> Initiative: [year]
> 상태: ⏳ 대기

## 개요

| 항목 | 내용 |
|------|------|
| **기간** | [YYYY-MM ~ YYYY-MM] |
| **목표** | [Phase 목표 한 줄 요약] |

## Goals

| Goal | 유형 | 상태 | 진행률 | 폴더 |
|------|------|------|--------|------|
| [goal-id]: [name] | [Feature|Enabler] | ⏳ 대기 | 0/N | [→](./goals/[goal-id]-[name]/) |

**Phase 진행률**: 0/N Goals 완료

## 완료 조건

- [ ] [goal별 완료 조건]
```

## Workflow

### Step 0. Setup
- [ ] `workspace/initiative/[year]/roadmap.md` 존재 확인
- [ ] roadmap.md에서 Phase에 배정된 Goals 확인
- [ ] `workspace/phase/[phase-id]/` 폴더 생성
- [ ] `workspace/phase/[phase-id]/goals/` 폴더 생성
- [ ] 상태 → 🔄

### Step 1. Create
- [ ] Phase README.md 작성 (개요, Goals 테이블, 완료 조건)
- [ ] 각 Goal 폴더 구조 생성 (`goals/[goal-id]-[name]/`)

### Step 2. Execute
<!-- Goals 표의 각 Goal에 대해 아래 블록을 반복 -->
#### Goal: {goal-id}-{name}
- [ ] writing-goal invoke
- [ ] Goal 상세화 + Epic 분해
- [ ] 모든 Epic 완료
<!-- /반복 -->
- [ ] 모든 Goal 완료 확인

### Step 3. Wrap-up
- [ ] 모든 Goal 상태 ✅ 확인
- [ ] 각 Goal의 catalog-transition 완료 확인 (`workspace/catalog/` 이동됨)
- [ ] SUMMARY.md 작성 (전체 Goal 성과, catalog 산출물 목록, 다음 Phase 전달 사항)
- [ ] RETRO.md 작성 (ref: [retro.md](retro.md))
- [ ] README.md 상태 → ✅, 진행률 갱신
- [ ] progress.md 갱신
- [ ] 다음 Phase 결정
