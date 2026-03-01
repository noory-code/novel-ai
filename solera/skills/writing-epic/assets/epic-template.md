# Template: _epic.md

## _epic.md

```markdown
# Epic: [명]

> Goal: [goal]
> 상태: ⏳ 대기

## 개요
| 항목 | 내용 |
|------|------|
| **유형** | Feature |
| **Journey** | [journey명] |

## 사용자 가치
**As a** [사용자],
**I want** [기능],
**So that** [가치].

## Stories
| ID | Story | 상태 |
|----|-------|------|
| US-001 | [제목] | ⏳ |

## 완료 조건
- [ ] 모든 Story 완료
```

## Workflow

### Step 0. Setup
- [ ] `goals/*/_goal.md` 존재 확인 → 없으면 writing-goal invoke
- [ ] `epic-[name]` 브랜치 생성 (from dev)
- [ ] 상태 → 🔄

### Step 1. Create
- [ ] Use Case 작성 → `artifacts/use-case/UC-NNN-[name].md`
- [ ] Concept 도출 → `artifacts/concept/domain.md`
- [ ] Entity 정의 → `artifacts/concept/entities/*.md`
- [ ] Story 분해 → `stories/[US|TS]-NNN/_story.md`
- [ ] `_epic.md` 작성 → Stories 표, 완료 조건

### Step 2. Execute
<!-- Stories 표의 각 Story에 대해 아래 블록을 반복 -->
#### Story: {US|TS}-NNN — {제목}
- [ ] writing-story invoke (Create → 브랜치 생성 → Execute → Wrap-up)
- [ ] Epic 브랜치에 머지
<!-- /반복 -->
- [ ] 모든 Story 완료 확인

### Step 3. Wrap-up
- [ ] 회고 작성 → RETRO.md (ref: [assets/retro.md](retro.md))
- [ ] 상태 → ✅
- [ ] workflow-pr invoke → 부모 브랜치로 PR 생성 + 머지
- [ ] 다음 Epic 결정 또는 Goal 완료 처리
