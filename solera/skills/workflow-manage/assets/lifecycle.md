# Lifecycle

모든 일감(Phase, Goal, Epic, Story, Action Item)은 `## Workflow` 섹션에 구체적 절차가 정의되어 있다.

## 핵심 원칙

- **SSOT**: 각 일감 템플릿의 `## Workflow`가 유일한 절차 원본
- **워크플로우 매니저는 읽고 실행**: 직접 정의하지 않는다

## Workflow 패턴

일감 Workflow는 Named Step 형태로 구성된다. 각 Step은 명확한 역할(Setup/Create/Execute/Wrap-up)을 갖는다.

```markdown
## Workflow

### Step 0. Setup
- [ ] 선행조건 확인 → 없으면 상위 스킬 invoke
- [ ] 브랜치 생성 (해당 시)
- [ ] 상태 → 🔄

### Step 1. Create
- [ ] ... (writing-* 스킬이 담당)

### Step 2. Execute
- [ ] ... 구체적 작업 단계들 ...

### Step 3. Wrap-up
- [ ] 완료 확인
- [ ] 상태 → ✅
- [ ] 다음 일감 결정
```

## 계층별 Workflow 위치

| 계층 | 템플릿 | Steps | Step 구성 |
|------|--------|-------|-----------|
| **Phase** | writing-phase/assets/phase-template.md | 4 | Setup → Create → Execute → Wrap-up |
| **Goal** | writing-goal/assets/goal-template.md | 4 | Setup → Create → Execute → Wrap-up |
| **Epic** | writing-epic/assets/epic-template.md | 4 | Setup → Create → Execute → Wrap-up |
| **Story** | writing-story/assets/story.md | 4 | Setup → Create → Execute → Wrap-up |
| **Action Item** | writing-action-item/assets/action-item.md | 3 | Setup → Execute → Wrap-up |

## 반복 블록 패턴

Execute Step에서 하위 일감을 반복 실행할 때, HTML 주석으로 반복 블록을 표기한다:

```markdown
### Step 2. Execute
<!-- Stories 표의 각 Story에 대해 아래 블록을 반복 -->
#### Story: {US|TS}-NNN — {제목}
- [ ] writing-story invoke
- [ ] Story 브랜치 생성
- [ ] 개발 + 완료
- [ ] Epic 브랜치에 머지
<!-- /반복 -->
- [ ] 모든 Story 완료 확인
```

- **템플릿**: `<!-- 반복 -->` ~ `<!-- /반복 -->` 사이에 1개 블록만 정의
- **실제 문서**: writing-* 스킬이 일감 생성 시 표의 항목 수만큼 블록을 확장
- **진행 체크**: 각 하위 일감마다 개별 체크박스가 생성되므로 진행 상황 추적 가능

## 워크플로우 매니저의 역할

1. 대상 일감의 `## Workflow` 읽기
2. 각 Step을 순서대로 실행
3. 문서 작성 필요 시 writing-* 스킬 invoke
4. 개발 작업 필요 시 frontend-*, dev-* 스킬 invoke
5. 완료 후 progress.md 업데이트 + 다음 일감 결정
