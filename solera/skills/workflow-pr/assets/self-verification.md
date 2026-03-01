# Validation: workflow-pr

> 이 파일은 workflow-pr 스킬의 고유 검증 규칙을 정의한다.

## Structural

```yaml
structural:
  - {id: S-001, name: "절차 섹션", type: section_exists, target: SKILL.md, section: "## 절차"}
  - {id: S-002, name: "Completion Checklist", type: section_exists, target: SKILL.md, section: "## Completion Checklist"}
  - {id: S-003, name: "PR 템플릿 존재", type: file_exists, paths: [assets/pr-template.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "gh pr create 명령", type: content_contains, target: SKILL.md, patterns: ["gh pr create"]}
  - {id: C-002, name: "리뷰 절차", type: content_contains, target: SKILL.md, patterns: ["리뷰"]}
  - {id: C-003, name: "머지 절차", type: content_contains, target: SKILL.md, patterns: ["머지"]}
  - {id: C-004, name: "브랜치 삭제", type: content_contains, target: SKILL.md, patterns: ["브랜치 삭제"]}
```
