# Template: Story

Epic의 분할 단위 (User Story/Technical Story)를 정의합니다.

## _story.md (User Story)

```markdown
# US-NNN: [제목]

> Epic: [상위 Epic명]
> 상태: ⏳ 대기 / 🔄 진행 / ✅ 완료 / ❌ 취소

## 사용자 스토리

**As a** [페르소나],
**I want** [행동],
**So that** [목적].

## 인수 조건

- [ ] [조건 1]
- [ ] [조건 2]

## Action Items

| ID | Action Item | Agent | Phase | depends_on | 상태 | 커밋 |
|----|-------------|-------|-------|------------|------|------|
| ACT-001 | [Action Item 제목] | [에이전트명 또는 -] | 1 | - | ⏳ 대기 | - |
| ACT-002 | [Action Item 제목] | [에이전트명 또는 -] | 1 | - | ⏳ 대기 | - |
| ACT-003 | [Action Item 제목] | [에이전트명 또는 -] | 2 | ACT-001,ACT-002 | ⏳ 대기 | - |

**진행률**: 0/N Action Items 완료
```

## _story.md (Technical Story)

```markdown
# TS-NNN: [제목]

> Epic: [상위 Epic명]
> 상태: ⏳ 대기 / 🔄 진행 / ✅ 완료 / ❌ 취소

## 기술 목표

[이 작업이 해결하는 기술적 문제/목표]

## 스펙

| 항목 | 내용 |
|------|------|
| **영향 범위** | [어떤 시스템에 영향] |
| **의존성** | [선행 작업/라이브러리] |

## 인수 조건

- [ ] [조건 1]
- [ ] [조건 2]

## Action Items

| ID | Action Item | Agent | Phase | depends_on | 상태 | 커밋 |
|----|-------------|-------|-------|------------|------|------|
| ACT-001 | [Action Item 제목] | [에이전트명 또는 -] | 1 | - | ⏳ 대기 | - |

**진행률**: 0/N Action Items 완료
```

## Workflow

### Step 0. Setup
- [ ] `epics/*/_epic.md` 존재 확인 → 없으면 writing-epic invoke
- [ ] 상태 → 🔄

### Step 1. Create (Epic 브랜치에서 수행)
- [ ] Story 유형 결정 (US / TS)
- [ ] 인수 조건 정의
- [ ] `_story.md` 작성 → 스토리/기술 목표, 인수 조건, Action Items 표
- [ ] Action Item 파일 생성 (필수) → `action-items/ACT-NNN-[name].md`
- [ ] Action Item별 담당 Agent 배정 (에이전트 팀 사용 시)
- [ ] Action Item 간 의존성(depends_on) 정의
- [ ] Phase 배분 (병렬 가능한 Action Items = 같은 Phase)
- [ ] `epic-[name]/story-[ID]-[name]` 브랜치 생성 (from Epic 브랜치)

### Step 2. Execute
<!-- Phase N의 Action Items를 병렬로 실행. 다음 Phase는 이전 Phase 완료 후 시작 -->
<!-- Action Items 표의 각 Action Item에 대해 아래 블록을 반복 -->
#### Action Item: ACT-NNN — {제목}
- [ ] writing-action-item invoke 또는 개발 스킬 invoke
- [ ] 작업 수행 + 커밋
<!-- /반복 -->
- [ ] 모든 인수 조건 충족 확인
- [ ] 모든 Action Item 완료 확인

### Step 3. Wrap-up
- [ ] 빌드/테스트 통과
- [ ] 회고 작성 → RETRO.md (ref: [assets/retro.md](retro.md))
- [ ] 상태 → ✅
- [ ] Epic 브랜치에 스쿼시 머지
- [ ] 다음 Story 결정 또는 Epic 완료 처리

## 폴더 구조

```
stories/[US|TS]-NNN/
├── _story.md
└── action-items/
    └── ACT-NNN-[name].md
```

## Story ID 규칙

| 접두어 | 유형 | 예시 |
|--------|------|------|
| `US-` | User Story | US-001, US-002 |
| `TS-` | Technical Story | TS-001, TS-002 |

> **주의**: Story ID는 **Epic 내**에서만 고유합니다.
> `login/US-001` ≠ `profile/US-001`

## 품질 기준

- [ ] User Story에 As a/I want/So that이 있는가?
- [ ] Technical Story에 기술 목표가 있는가?
- [ ] 인수 조건이 정의되어 있는가?
- [ ] 모든 Action Item에 ID가 부여되어 있는가?
- [ ] 진행률이 표시되어 있는가?
- [ ] Action Item별 Agent/Phase/depends_on이 정의되어 있는가?
- [ ] 같은 Phase의 Action Items가 산출물 충돌 없이 병렬 실행 가능한가?
