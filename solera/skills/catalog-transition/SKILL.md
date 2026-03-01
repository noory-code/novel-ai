---
name: catalog-transition
description: Goal 완료 시 artifacts를 published로 전환
metadata:
  version: "3.0.0"
  category: workflow
  type: composite
  style: procedural
  triggers: [catalog 전환, artifacts 이동, Goal 완료 정리]
  uses: []
---

# Catalog Transition

## 선행조건

- Goal 상태 완료 → 모든 Story 완료 필요
- 모든 Epic 완료 → 미완료 시 진행 불가

## 입력

| 파라미터 | 필수 | 설명 | 예시 |
|----------|------|------|------|
| **goal_path** | Y | 완료된 Goal 경로 | goals/G1-liquor-search |

## 산출물

| Step | 산출물 | 경로 |
|------|--------|------|
| 파일 이동 | 전환된 산출물 | `published/{type}/` |
| 버전 기록 | 버전 태그 | 문서 헤더에 `[Phase]-[Goal번호]` |

## 절차

1. **전환 대상 확인**
   - [ ] `goals/[goal]/artifacts/` 스캔
   - [ ] 이동 매핑표에 정의된 타입의 파일만 선택 (매핑표에 없는 파일은 제외)

2. **버전 기록**
   - [ ] 헤더에 `적용 버전: [Phase]-[Goal번호]` 추가
   - [ ] 형식: H1-G01, H1-G02 등

3. **파일 이동**
   - [ ] 이동 매핑표에 따라 파일 이동

4. **링크 업데이트**
   - [ ] _goal.md, 다른 산출물의 경로 수정

5. **Obsidian 최적화**
   - [ ] frontmatter에 적용 버전 추가
   - [ ] status/* 태그 → status/completed
   - [ ] updated 날짜 갱신

6. **검증**
   - [ ] 모든 파일 published에 이동됨
   - [ ] 버전 정보 기록됨
   - [ ] 링크 정상 동작
   - [ ] artifacts 폴더 비어있음

---

## 버전 형식

| 패턴 | 예시 |
|------|------|
| `[Phase]-[Goal번호]` | H1-G01, H1-G02, H2-G01 |

**문서 헤더 예시**:
```markdown
# Journey: alba-first-search

> Persona: ALBA
> 적용 버전: H1-G01
> 마지막 업데이트: 2026-01-15
```

## 이동 매핑

| 산출물 | 이동 위치 |
|--------|----------|
| service-map | `published/service-map/` |
| persona | `published/persona/` |
| journey | `published/journey/` |
| use-case | `published/use-case/` |
| concept | `published/concept/` |
| erd | `published/schema/` |
| dto | `published/dto/` |
| api-spec | `published/api/` |

## Obsidian Frontmatter

```yaml
---
title: [문서 제목]
type: [journey|persona|service|concept|schema|use-case]
tags:
  - status/completed    # 완료 상태로 변경
  - relates-to/[연관문서]
created: YYYY-MM-DD
updated: YYYY-MM-DD      # 전환일로 갱신
적용버전: [Phase]-[Goal번호]
---
```

## 예시

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

### After (published/)

```
published/
├── service-map/
│   └── index.md           # 적용 버전: H1-G01
├── persona/
│   ├── bana.md            # 적용 버전: H1-G01
│   └── relationship.md    # 적용 버전: H1-G01
├── journey/
│   └── first-search.md    # 적용 버전: H1-G01
├── use-case/
│   └── UC-001-search-liquor.md  # 적용 버전: H1-G01
└── concept/
    └── liquor.md          # 적용 버전: H1-G01
```

## 주의사항

- published에는 이동 매핑표에 정의된 타입만 이동 (매핑표에 없는 파일은 artifacts에 잔류)
- 동일 파일 존재 시 버전이 높은 것으로 교체
- 이전 버전 확인이 필요하면 `git log --follow -- {파일경로}`로 히스토리 조회
- Goal 단위로 일괄 전환 (Epic 단위 아님)

## References

### 검증

| 파일 | 내용 |
|------|------|
| [self-verification.md](assets/self-verification.md) | 스킬 정의 자동 검증 TC (9건) |

## Completion Checklist

- [ ] 전환 대상 확인됨
- [ ] 버전 기록 추가됨
- [ ] 파일 이동 완료
- [ ] 링크 업데이트됨
- [ ] Obsidian frontmatter 최적화됨
- [ ] 검증 완료 (링크 정상, artifacts 비어있음)
