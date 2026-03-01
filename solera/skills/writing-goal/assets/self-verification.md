# Validation: writing-goal

> 이 파일은 writing-goal 스킬의 고유 검증 규칙을 정의한다.

## Structural

```yaml
structural:
  - {id: S-001, name: "Workflow 섹션", type: section_exists, target: assets/goal-template.md, section: "## Workflow"}
  - {id: S-002, name: "Step 0 Setup", type: content_contains, target: assets/goal-template.md, patterns: ["### Step 0. Setup"]}
  - {id: S-003, name: "Step 4단계", type: count_check, target: assets/goal-template.md, pattern: "### Step \\d+", min: 4, max: 4}
  - {id: S-004, name: "goal-template 존재", type: file_exists, paths: [assets/goal-template.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "Epic 반복 블록", type: content_contains, target: assets/goal-template.md, patterns: ["writing-epic invoke", "<!-- /반복 -->"]}
  - {id: C-002, name: "Goal 유형 섹션", type: section_exists, target: assets/goal-template.md, section: "## Goal 유형"}
  - {id: C-003, name: "산출물 템플릿", type: file_exists, paths: [assets/goal-template.md, assets/persona.md, assets/service-map.md]}
  - {id: C-004, name: "retro.md 존재", type: file_exists, paths: [assets/retro.md]}
  - {id: C-005, name: "회고 ref 존재", type: content_contains, target: assets/goal-template.md, patterns: ["retro.md"]}
  - {id: C-006, name: "상태 전이 포함", type: content_contains, target: assets/goal-template.md, patterns: ["상태 →"]}
  - {id: C-007, name: "catalog-transition 참조", type: content_contains, target: assets/goal-template.md, patterns: ["catalog-transition"]}
  - {id: C-008, name: "Enabler 분기", type: content_contains, target: assets/goal-template.md, patterns: ["Enabler"]}
  - {id: C-009, name: "입력 테이블", type: content_contains, target: SKILL.md, patterns: ["project_path"]}
  - {id: C-010, name: "Wrap-up 절차", type: content_contains, target: SKILL.md, patterns: ["Wrap-up"]}
  - {id: C-011, name: "사용 스킬 테이블", type: section_exists, target: SKILL.md, section: "## 사용 스킬"}
  - {id: C-012, name: "persona-relationship 참조", type: content_contains, target: SKILL.md, patterns: ["persona-relationship"]}
```
