# Template: Action Item

Story의 분할 단위 = 커밋 단위를 정의합니다.

## ACT-NNN-[name].md

```markdown
# ACT-NNN: [제목]

> Story: [US|TS]-NNN
> 상태: ⏳ 대기 / 🔄 진행 / ✅ 완료 / ❌ 취소
> Agent: [fullstack-db | fullstack-domain | fullstack-data | fullstack-presentation | -]
> Phase: [N]
> depends_on: [ACT-NNN, ...] 또는 -
> output_paths: [예상 산출 파일 경로]

## 목표

[이 Action Item이 달성하려는 것]

## 작업 내용

- [ ] [작업 1]
- [ ] [작업 2]

---

## 결과 (완료 후 기록)

### 변경 파일

- `path/to/file.dart` - [변경 내용]

### 커밋

- `abc1234` [epic-name][US-NNN][ACT-NNN] 제목
```

## Workflow

### Step 0. Setup
- [ ] `stories/[US|TS]-NNN/_story.md` 존재 확인 → 없으면 writing-story invoke
- [ ] 상태 → 🔄
- [ ] 목표 확인 + 작업 내용 체크리스트 확인

### Step 1. Execute
- [ ] 필요 스킬 파악 → 개발 스킬 invoke (frontend-*, dev-*, design-* 등)
- [ ] 실제 코딩/문서 작업 수행
- [ ] 작업 내용 체크리스트 전부 완료 확인

### Step 2. Wrap-up
- [ ] 빌드/테스트 통과 (해당 시)
- [ ] 변경 파일 목록 기록
- [ ] 커밋 (1 Action Item = 1 커밋, 메시지 형식 준수)
- [ ] 회고 작성 → RETRO.md (ref: [assets/retro.md](retro.md))
- [ ] 상태 → ✅
- [ ] 다음 Action Item 결정 또는 Story 완료 처리

## 폴더 구조

```
stories/[US|TS]-NNN/action-items/
└── ACT-NNN-[name].md
```

## 커밋 메시지 형식

```
[epic-name][US-NNN][ACT-NNN] 제목

- 변경 내용 1
- 변경 내용 2
```

**예시:**
```
[define-concept][TS-001][ACT-001] 도메인 개념 정의
[design-schema][TS-001][ACT-002] ERD 작성
```

## 주의 사항

| 틀린 것 | 맞는 것 |
|---------|---------|
| Action Item마다 브랜치 생성 | Action Item = **커밋**만 |
| 여러 Action Item을 하나의 커밋으로 | Action Item 1개 = 커밋 1개 |
