# Validation: writing-phase

> 이 파일은 writing-phase 스킬의 고유 검증 규칙을 정의한다.

## Structural

```yaml
structural:
  - {id: S-001, name: "Workflow 섹션", type: section_exists, target: assets/phase-template.md, section: "## Workflow"}
  - {id: S-002, name: "Step 0 Setup", type: content_contains, target: assets/phase-template.md, patterns: ["### Step 0. Setup"]}
  - {id: S-003, name: "Step 4단계", type: count_check, target: assets/phase-template.md, pattern: "### Step \\d+", min: 4, max: 4}
  - {id: S-004, name: "phase-template 존재", type: file_exists, paths: [assets/phase-template.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "Goal 반복 블록", type: content_contains, target: assets/phase-template.md, patterns: ["writing-goal invoke", "<!-- /반복 -->"]}
  - {id: C-002, name: "retro.md 존재", type: file_exists, paths: [assets/retro.md]}
  - {id: C-003, name: "회고 ref 존재", type: content_contains, target: assets/phase-template.md, patterns: ["retro.md"]}
  - {id: C-004, name: "상태 전이 포함", type: content_contains, target: assets/phase-template.md, patterns: ["상태 →"]}
  - {id: C-005, name: "roadmap 선행조건", type: content_contains, target: SKILL.md, patterns: ["roadmap.md"]}
  - {id: C-006, name: "Phase 폴더 구조", type: section_exists, target: SKILL.md, section: "## 폴더 구조"}
  - {id: C-007, name: "입력 테이블", type: content_contains, target: SKILL.md, patterns: ["project_path"]}
  - {id: C-008, name: "Wrap-up catalog 확인", type: content_contains, target: assets/phase-template.md, patterns: ["catalog-transition"]}
  - {id: C-009, name: "SUMMARY.md 언급", type: content_contains, target: assets/phase-template.md, patterns: ["SUMMARY.md"]}
```
