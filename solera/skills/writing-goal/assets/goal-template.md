# Template: _goal.md

## _goal.md

```markdown
# Goal: [명]

> Phase: [phase]
> 상태: ⏳ 대기

## Journey (러프)

| Journey | Persona | Steps |
|---------|---------|-------|
| [name] | [persona] | Step1 → Step2 → Step3 |

## Epics

| Epic | Journey | 상태 |
|------|---------|------|
| 01-[name] | [journey] | ⏳ |

## 완료 조건

- [ ] 모든 Epic 완료
```

## Workflow

### Step 0. Setup
- [ ] `published/identity/mission.md` 존재 확인 → 없으면 writing-identity invoke
- [ ] `goals/[goal-id]-[name]/` 폴더 생성
- [ ] `goals/[goal-id]-[name]/artifacts/` 폴더 생성
- [ ] 상태 → 🔄

### Step 1. Create
- [ ] Service Map, Persona 생성 (Feature만, Enabler는 건너뜀)
- [ ] Journey (러프) 작성 → Persona별 Steps 순서
- [ ] Epic 분해 → Journey와 매핑, 번호 부여 (01, 02, ...)
- [ ] `_goal.md` 작성 → Journey 표, Epics 표, 완료 조건

### Step 2. Execute
<!-- Epics 표의 각 Epic에 대해 아래 블록을 반복 -->
#### Epic: {번호}-{name}
- [ ] writing-epic invoke (Setup → Create → Execute → Wrap-up)
- [ ] workflow-pr invoke → 부모 브랜치로 PR
<!-- /반복 -->
- [ ] 모든 Epic 완료 확인

### Step 3. Wrap-up
- [ ] 회고 작성 → RETRO.md (ref: [assets/retro.md](retro.md))
- [ ] 상태 → ✅
- [ ] catalog-transition invoke (artifacts/ → published/)

## Goal 유형

| 유형 | 산출물 | 예시 |
|------|--------|------|
| **Feature** | Service Map, Persona, Journey → Epic | 주류검색, 프로필 |
| **Enabler** | Epic (Persona/Journey 생략 가능) | 인프라, DB설계 |
