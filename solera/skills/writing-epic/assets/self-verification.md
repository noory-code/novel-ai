# Validation: writing-epic

> 이 파일은 writing-epic 스킬의 고유 검증 규칙을 정의한다.

## Structural

```yaml
structural:
  - {id: S-001, name: "Workflow 섹션", type: section_exists, target: assets/epic-template.md, section: "## Workflow"}
  - {id: S-002, name: "Step 0 Setup", type: content_contains, target: assets/epic-template.md, patterns: ["### Step 0. Setup"]}
  - {id: S-003, name: "Step 4단계", type: count_check, target: assets/epic-template.md, pattern: "### Step \\d+", min: 4, max: 4}
  - {id: S-004, name: "epic-template 존재", type: file_exists, paths: [assets/epic-template.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "Story 반복 블록", type: content_contains, target: assets/epic-template.md, patterns: ["writing-story invoke", "<!-- /반복 -->"]}
  - {id: C-002, name: "산출물 템플릿", type: file_exists, paths: [assets/epic-template.md, assets/use-case.md, assets/entity.md, assets/concept.md]}
  - {id: C-003, name: "retro.md 존재", type: file_exists, paths: [assets/retro.md]}
  - {id: C-004, name: "회고 ref 존재", type: content_contains, target: assets/epic-template.md, patterns: ["retro.md"]}
  - {id: C-005, name: "상태 전이 포함", type: content_contains, target: assets/epic-template.md, patterns: ["상태 →"]}
  - {id: C-006, name: "Use Case 산출물", type: content_contains, target: assets/epic-template.md, patterns: ["use-case"]}
  - {id: C-007, name: "Entity 산출물", type: content_contains, target: assets/epic-template.md, patterns: ["entities"]}
  - {id: C-008, name: "선행조건에 Goal 컨텍스트", type: content_contains, target: SKILL.md, patterns: ["_goal.md", "published/identity/mission.md"]}
  - {id: C-009, name: "Wrap-up 절차 존재", type: content_contains, target: SKILL.md, patterns: ["Wrap-up", "RETRO.md", "workflow-pr"]}
  - {id: C-010, name: "사용 스킬 테이블", type: section_exists, target: SKILL.md, section: "## 사용 스킬"}
```
