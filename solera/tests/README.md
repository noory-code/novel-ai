# 스킬 검증 테스트

## 개요

이 테스트 스위트는 Solera 워크플로우 스킬의 파라미터 검증을 자동화합니다.

## 검증 항목

### 1. 필수 파라미터 검증
- 스킬이 필수 파라미터 없이 호출되는 것을 방지
- solera-write-story: project_path, phase_id, goal_id, epic_name, story_id, story_name
- solera-execute-action-item: epic_name, story_id, action_item_id, action_item_name

### 2. 파라미터 형식 검증
- phase_id: `YYYY-PX-name` (예: 2026-P1-foundation)
- goal_id: `GX-name` (예: G1-search-liquor)
- story_id: `US-NNN` 또는 `TS-NNN` (예: US-001)
- action_item_id: `ACT-NNN` (예: ACT-001)

### 3. Prerequisites 검증
- 스킬 실행 전 필수 조건 확인
- solera-write-story: mission.md, _epic.md 존재 여부
- solera-execute-action-item: _story.md 존재, 의존 ACT 완료 여부

### 4. 출력 검증
- 스킬이 예상된 출력을 생성하는지 확인
- solera-write-story: _story.md, ACT-NNN-{name}.md, RETRO.md
- solera-execute-action-item: 코드 변경, git commit, 상태 업데이트

### 5. 커밋 메시지 형식 검증
- 형식: `[epic-name][US-NNN][ACT-NNN] title`
- 예: `[01-auth][US-001][ACT-001] 로그인 폼 생성`

## 실행 방법

### 직접 실행
```bash
python3 tests/test_skill_validation.py
```

### pytest로 실행 (권장)
```bash
pytest tests/test_skill_validation.py -v
```

### 모든 테스트 실행
```bash
pytest tests/ -v
```

## 테스트 추가

새로운 스킬을 추가할 때는 `test_skill_validation.py`에 해당 스킬의 검증 테스트를 추가하세요:

1. `test_{skill_name}_required_parameters()` - 필수 파라미터
2. `test_{skill_name}_parameter_formats()` - 형식 검증
3. `test_{skill_name}_prerequisites()` - Prerequisites
4. `test_{skill_name}_expected_outputs()` - 출력 검증

## 의존성

- Python 3.8+
- pytest (선택사항, 더 나은 테스트 리포트를 위해 권장)

```bash
pip install pytest
```
