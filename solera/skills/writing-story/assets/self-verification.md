# Validation: writing-story

> 이 파일은 writing-story 스킬의 고유 검증 규칙을 정의한다.

## Structural

```yaml
structural:
  - {id: S-001, name: "Workflow 섹션", type: section_exists, target: assets/story.md, section: "## Workflow"}
  - {id: S-002, name: "Step 0 Setup", type: content_contains, target: assets/story.md, patterns: ["### Step 0. Setup"]}
  - {id: S-003, name: "Step 4단계", type: count_check, target: assets/story.md, pattern: "### Step \\d+", min: 4, max: 4}
  - {id: S-004, name: "story 템플릿 존재", type: file_exists, paths: [assets/story.md]}
  - {id: S-005, name: "retro 템플릿 존재", type: file_exists, paths: [assets/retro.md]}
```

## Semantic

```yaml
semantic:
  - {id: C-001, name: "Action Item 반복 블록", type: content_contains, target: assets/story.md, patterns: ["writing-action-item invoke", "<!-- /반복 -->"]}
  - {id: C-002, name: "US/TS 구분", type: content_contains, target: assets/story.md, patterns: ["User Story", "Technical Story"]}
  - {id: C-003, name: "품질 기준 섹션", type: section_exists, target: assets/story.md, section: "## 품질 기준"}
  - {id: C-004, name: "Story ID 규칙", type: section_exists, target: assets/story.md, section: "## Story ID 규칙"}
  - {id: C-005, name: "상태 전이 포함", type: content_contains, target: assets/story.md, patterns: ["상태 →"]}
  - {id: C-006, name: "폴더 구조 섹션", type: section_exists, target: assets/story.md, section: "## 폴더 구조"}
  - {id: C-007, name: "인수 조건 패턴", type: content_contains, target: assets/story.md, patterns: ["## 인수 조건"]}
  - {id: C-008, name: "회고 작성 참조", type: content_contains, target: assets/story.md, patterns: ["회고 작성", "RETRO.md"]}
  - {id: C-009, name: "스쿼시 머지", type: content_contains, target: assets/story.md, patterns: ["스쿼시 머지"]}
  - {id: C-010, name: "Action Items 에이전트 컬럼", type: content_contains, target: assets/story.md, patterns: ["Agent", "Phase", "depends_on"]}
  - {id: C-011, name: "retro 템플릿 참조", type: content_contains, target: assets/story.md, patterns: ["retro.md"]}
  - {id: C-012, name: "선행조건에 Epic 컨텍스트", type: content_contains, target: SKILL.md, patterns: ["_epic.md", "published/identity/mission.md"]}
  - {id: C-013, name: "Wrap-up 절차 존재", type: content_contains, target: SKILL.md, patterns: ["Wrap-up", "RETRO.md", "스쿼시 머지"]}
  - {id: C-014, name: "사용 스킬 테이블", type: section_exists, target: SKILL.md, section: "## 사용 스킬"}
```
