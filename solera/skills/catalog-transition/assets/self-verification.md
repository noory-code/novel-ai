# Validation: catalog-transition

> 이 파일은 catalog-transition 스킬의 고유 검증 규칙을 정의한다.

## Structural

```yaml
structural:
  - id: S-001
    name: "선행조건 섹션 존재"
    type: section_exists
    target: SKILL.md
    section: "## 선행조건"

  - id: S-002
    name: "절차 섹션 존재"
    type: section_exists
    target: SKILL.md
    section: "## 절차"

  - id: S-003
    name: "Completion Checklist 존재"
    type: section_exists
    target: SKILL.md
    section: "## Completion Checklist"

  - id: S-004
    name: "버전 형식 섹션 존재"
    type: section_exists
    target: SKILL.md
    section: "## 버전 형식"

  - id: S-005
    name: "이동 매핑 섹션 존재"
    type: section_exists
    target: SKILL.md
    section: "## 이동 매핑"
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
      - "catalog"
      - "artifacts"
      - "적용 버전"
      - "Goal"

  - id: C-003
    name: "버전 패턴 정의"
    type: content_contains
    target: SKILL.md
    patterns:
      - "[Phase]-[Goal번호]"
      - "H1-G01"

  - id: C-004
    name: "절차 단계 체크리스트"
    type: count_check
    target: SKILL.md
    pattern: "- \\[ \\]"
    min: 5
    max: 999
```
