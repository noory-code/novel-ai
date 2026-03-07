---
name: transition-catalog
description: Mark a Goal as done — move all artifacts to the published catalog and update cross-references.
metadata:
  version: "4.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [transition to catalog, archive completed Goal, publish Goal artifacts, wrap up Goal, Goal completion cleanup]
  uses: []
---

# Catalog Transition

## Prerequisites

- Goal status is complete — all Stories must be complete
- All Epics are complete — cannot proceed if any are incomplete

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **goal_path** | Y | Path of the completed Goal | goals/G1-liquor-search |

## Output

| Step | Output | Path | Nature |
|------|--------|------|--------|
| File move | Transitioned artifacts | `workspace/catalog/published/{type}/` | Final |
| Version record | Version tag | `[Phase]-[Goal number]` in document header | Final |

## Procedure

1. **Confirm transition targets**
   - [ ] Scan `goals/[goal]/artifacts/`
   - [ ] Select only files of types defined in the move mapping table (exclude any files not in the mapping table)

2. **Record version**
   - [ ] Add `Applied version: [Phase]-[Goal number]` to the header
   - [ ] Format: H1-G01, H1-G02, etc.

3. **Move files**
   - [ ] Move files according to the move mapping table

4. **Update links**
   - [ ] Fix paths in _goal.md and other artifacts

5. **Obsidian optimization**
   - [ ] Add the applied version to frontmatter
   - [ ] Change status/* tags to status/completed
   - [ ] Update the `updated` date

6. **Verification**
   - [ ] All files moved to published
   - [ ] Version information recorded
   - [ ] Links are working correctly
   - [ ] The artifacts folder is empty

---

## Version Format

| Pattern | Example |
|---------|---------|
| `[Phase]-[Goal number]` | H1-G01, H1-G02, H2-G01 |

**Document header example**:
```markdown
# Journey: alba-first-search

> Persona: ALBA
> Applied version: H1-G01
> Last updated: 2026-01-15
```

## Move Mapping

| Artifact | Destination |
|----------|------------|
| service-map | `workspace/catalog/published/service-map/` |
| persona | `workspace/catalog/published/persona/` |
| journey | `workspace/catalog/published/journey/` |
| use-case | `workspace/catalog/published/use-case/` |
| concept | `workspace/catalog/published/concept/` |
| erd | `workspace/catalog/published/schema/` |
| dto | `workspace/catalog/published/dto/` |
| api-spec | `workspace/catalog/published/api/` |

## Obsidian Frontmatter

> **Note:** This section is for teams using Obsidian as a knowledge base. If you are not using Obsidian, skip the frontmatter fields — the file move in step 3 is the only required action.

```yaml
---
title: [document title]
type: [journey|persona|service|concept|schema|use-case]
tags:
  - status/completed    # changed to completed status
  - relates-to/[related document]
created: YYYY-MM-DD
updated: YYYY-MM-DD      # updated to transition date
applied-version: [Phase]-[Goal number]
---
```

## Example

### Before (artifacts/)

```
goals/G1-liquor-search/artifacts/
├── service-map/
│   └── index.md
├── persona/
│   ├── bana.md
│   └── relationship.md
├── journey/
│   └── first-search.md
├── use-case/
│   └── UC-001-search-liquor.md
└── concept/
    └── liquor.md
```

### After (workspace/catalog/published/)

```
workspace/catalog/published/
├── service-map/
│   └── index.md           # Applied version: H1-G01
├── persona/
│   ├── bana.md            # Applied version: H1-G01
│   └── relationship.md    # Applied version: H1-G01
├── journey/
│   └── first-search.md    # Applied version: H1-G01
├── use-case/
│   └── UC-001-search-liquor.md  # Applied version: H1-G01
└── concept/
    └── liquor.md          # Applied version: H1-G01
```

## Notes

- Only move types defined in the move mapping table to `workspace/catalog/published/` (files not in the mapping table remain in artifacts)
- If the same file already exists in the destination, replace it with the higher version
- To review a previous version, use `git log --follow -- {file-path}` to view history
- Transition in bulk by Goal, not by Epic

## References

### Verification

| File | Content |
|------|---------|
| [self-verification.md](assets/self-verification.md) | Automated skill definition verification TCs (9 cases) |

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| Goal 미완료 | 일부 Story 상태가 ✅ 아님 | 미완료 Story 목록 출력, 완료 요청 | 스킬 중단, 모든 Story 완료 후 재개 |
| Epic 미완료 | 일부 Epic 상태가 ✅ 아님 | 미완료 Epic 목록 출력, 완료 요청 | 스킬 중단, 모든 Epic 완료 후 재개 |
| artifacts 폴더 없음 | `goals/{goal}/artifacts/` 없음 | 경고 메시지 출력, 전환 대상 없음으로 처리 | 스킬 완료 (전환 불필요) |
| 매핑 테이블 외 파일 발견 | artifacts에 매핑 테이블에 없는 타입 존재 | 제외 파일 목록 출력, artifacts에 남김 | 계속 진행 (매핑된 파일만 이동) |
| catalog 디렉토리 없음 | `workspace/catalog/published/` 없음 | `mkdir -p` 로 디렉토리 생성 | 디렉토리 생성 후 계속 진행 |
| 파일 이동 실패 | 권한 오류 또는 경로 문제 | 실패한 파일 목록 출력, 권한 확인 요청 | 스킬 중단, 수동 처리 후 재개 |
| 링크 업데이트 실패 | 상대 경로 변환 오류 | 수정 필요 링크 목록 출력, 수동 수정 요청 | Verification 단계 중단, 수동 수정 후 재개 |
| frontmatter 파싱 실패 | YAML 형식 오류 | 해당 파일 건너뛰고 경고 출력 | 계속 진행 (frontmatter 업데이트는 선택 사항) |
| artifacts 폴더 비지 않음 | 매핑되지 않은 파일 남음 | 남은 파일 목록 출력, 의도적인지 확인 요청 | 스킬 완료 (검증 경고 포함) |

## Completion Checklist

- [ ] Transition targets confirmed
- [ ] Version record added
- [ ] File move complete
- [ ] Links updated
- [ ] Obsidian frontmatter optimized
- [ ] Verification complete (links working, artifacts empty)
