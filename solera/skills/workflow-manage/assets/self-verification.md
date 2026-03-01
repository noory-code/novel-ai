# Validation: workflow-manage

> 이 파일은 workflow-manage 스킬의 고유 검증 규칙을 정의한다.

## Structural

```yaml
structural:
  - id: S-001
    name: "공통 규칙 섹션 존재"
    type: section_exists
    target: SKILL.md
    section: "## 공통 규칙"

  - id: S-002
    name: "선행조건 섹션 존재"
    type: section_exists
    target: SKILL.md
    section: "## 선행조건"

  - id: S-003
    name: "절차 섹션 존재"
    type: section_exists
    target: SKILL.md
    section: "## 절차"

  - id: S-004
    name: "Completion Checklist 존재"
    type: section_exists
    target: SKILL.md
    section: "## Completion Checklist"

  - id: S-005
    name: "assets 파일 존재"
    type: file_exists
    paths:
      - assets/conventions.md
      - assets/lifecycle.md
      - assets/progress.md
      - assets/retro.md
      - assets/status.md
```

## Semantic

```yaml
semantic:
  - id: C-001
    name: "AI-First 금지 표현 없음"
    type: content_not_contains
    target: SKILL.md
    patterns:
      - "적절히"
      - "필요시"
      - "상황에 따라"
      - "알아서"

  - id: C-002
    name: "핵심 키워드 포함"
    type: content_contains
    target: SKILL.md
    patterns:
      - "Workflow"
      - "progress.md"
      - "RETRO.md"
      - "일감"

  - id: C-003
    name: "절차 단계 정의"
    type: content_contains
    target: SKILL.md
    patterns:
      - "### start"
      - "### complete"
      - "### check"
      - "### next"

  - id: C-004
    name: "스킬 위임 명시"
    type: content_contains
    target: SKILL.md
    patterns:
      - "writing-*"
      - "invoke"

  - id: C-005
    name: "역할 분담 표 존재"
    type: section_exists
    target: SKILL.md
    section: "## 역할 분담"

  - id: C-006
    name: "감독 원칙 존재"
    type: section_exists
    target: SKILL.md
    section: "## 감독 원칙"
```
