# Validation: writing-action-item

> 이 파일은 writing-action-item 스킬의 고유 검증 규칙을 정의한다.

## Structural

```yaml
structural:
  - {id: S-001, name: "Workflow 섹션", type: section_exists, target: assets/action-item.md, section: "## Workflow"}
  - {id: S-002, name: "Step 0 Setup", type: content_contains, target: assets/action-item.md, patterns: ["### Step 0. Setup"]}
  - {id: S-003, name: "Step 3단계", type: count_check, target: assets/action-item.md, pattern: "### Step \\d+", min: 3, max: 3}
  - {id: S-004, name: "action-item 템플릿 존재", type: file_exists, paths: [assets/action-item.md]}
  - {id: S-005, name: "retro 템플릿 존재", type: file_exists, paths: [assets/retro.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "1 AI = 1 커밋", type: content_contains, target: SKILL.md, patterns: ["1 Action Item = 1 커밋"]}
  - {id: C-002, name: "커밋 메시지 형식", type: content_contains, target: assets/action-item.md, patterns: ["[epic-name]"]}
  - {id: C-003, name: "상태 전이 포함", type: content_contains, target: assets/action-item.md, patterns: ["상태 →"]}
  - {id: C-004, name: "주의 사항 섹션", type: section_exists, target: assets/action-item.md, section: "## 주의 사항"}
  - {id: C-005, name: "폴더 구조 섹션", type: section_exists, target: assets/action-item.md, section: "## 폴더 구조"}
  - {id: C-006, name: "커밋 메시지 형식 섹션", type: section_exists, target: assets/action-item.md, section: "## 커밋 메시지 형식"}
  - {id: C-007, name: "회고 작성 참조", type: content_contains, target: assets/action-item.md, patterns: ["회고 작성", "RETRO.md"]}
  - {id: C-008, name: "에이전트 배정 메타데이터", type: content_contains, target: assets/action-item.md, patterns: ["Agent:", "Phase:", "depends_on:"]}
  - {id: C-009, name: "output_paths 메타데이터", type: content_contains, target: assets/action-item.md, patterns: ["output_paths"]}
  - {id: C-010, name: "선행조건에 Story 컨텍스트", type: content_contains, target: SKILL.md, patterns: ["_story.md", "depends_on"]}
  - {id: C-011, name: "사용 스킬 테이블", type: section_exists, target: SKILL.md, section: "## 사용 스킬"}
```
