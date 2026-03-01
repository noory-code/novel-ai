---
name: writing-phase
description: Phase 문서 작성. Initiative의 Goals를 분기별로 배분 → Goal 실행 추적. Triggers - "Phase 정의", "Phase 시작", "분기 계획".
metadata:
  version: "2.0.0"
  category: writing
  type: composite
  style: procedural
  triggers: [Phase 정의, Phase 시작, 분기 계획]
  uses: [writing-goal]
---

# Writing Phase

> Phase README.md를 작성하고, Goal 실행을 추적한다.

## 선행조건

- `workspace/initiative/[year]/roadmap.md` 존재 → 없으면 사용자에게 요청

## 입력

| 파라미터 | 필수 | 설명 | 예시 |
|----------|------|------|------|
| **phase_id** | Y | Phase ID | 2026-P1-foundation |
| **year** | Y | Initiative 연도 | 2026 |
| **project_path** | Y | 프로젝트 workspace 루트 | banas/workspace |

## 산출물

| Step | 산출물 | 경로 |
|------|--------|------|
| Create | Phase README | `{project_path}/phase/{phase_id}/README.md` |
| Create | Goal 폴더 구조 | `{project_path}/phase/{phase_id}/goals/{goal_id}-{name}/` |
| Wrap-up | Phase 요약 | `{project_path}/phase/{phase_id}/SUMMARY.md` |
| Wrap-up | Phase 회고 | `{project_path}/phase/{phase_id}/RETRO.md` |
| Wrap-up | progress.md 갱신 | `{project_path}/progress.md` |

## 사용 스킬

| 스킬 | 용도 | Step |
|------|------|------|
| `writing-goal` | 각 Goal 상세화 및 Epic 분해 | Execute |
| `catalog-transition` | Goal 완료 시 artifacts → catalog 이동 | Execute (Goal 내부) |

## 절차

1. **roadmap 확인**
   - [ ] `{project_path}/initiative/{year}/roadmap.md` 읽기
   - [ ] Phase 계획 테이블에서 해당 Phase의 Goals 목록 추출
   - [ ] Goals 없음 → 사용자에게 확인

2. **Phase 폴더 생성**
   - [ ] `{project_path}/phase/{phase_id}/` 생성
   - [ ] `{project_path}/phase/{phase_id}/goals/` 생성

3. **README.md 작성** → ref: [assets/phase-template.md](assets/phase-template.md)
   - [ ] 개요 테이블 (기간, 목표)
   - [ ] Goals 테이블 (roadmap에서 추출한 Goals)
   - [ ] 완료 조건 (Goal별 핵심 조건)
   - [ ] Workflow 섹션 (템플릿 그대로)

4. **Goal 폴더 구조 생성**
   - [ ] 각 Goal에 대해 `goals/{goal_id}-{name}/` 생성
   - [ ] writing-goal invoke 준비

5. **Phase Wrap-up**
   - [ ] 모든 Goal 상태 ✅ 확인
   - [ ] 각 Goal의 catalog-transition 완료 확인 (`workspace/catalog/` 이동됨)
   - [ ] SUMMARY.md 작성 (전체 Goal 성과, catalog 산출물 목록, 다음 Phase 전달 사항)
   - [ ] RETRO.md 작성 → ref: [assets/retro.md](assets/retro.md)
   - [ ] README.md 상태 → ✅, 진행률 갱신
   - [ ] progress.md 갱신

## 폴더 구조

```
{project_path}/phase/{phase_id}/
├── README.md
├── SUMMARY.md      # Wrap-up 시 생성 (템플릿 TBD)
├── RETRO.md        # Wrap-up 시 생성
└── goals/
    ├── {goal_id}-{name}/
    │   ├── _goal.md
    │   ├── artifacts/    # Goal 진행 중 → catalog-transition으로 이동
    │   └── epics/
    └── ...
```

## Completion Checklist

- [ ] README.md 생성 완료
- [ ] Goals 테이블에 roadmap의 모든 Goal 포함
- [ ] 각 Goal 폴더 구조 생성
- [ ] writing-goal 전환 준비
- [ ] (Wrap-up) 모든 Goal catalog-transition 완료 확인
- [ ] (Wrap-up) SUMMARY.md 작성
- [ ] (Wrap-up) RETRO.md 작성
- [ ] (Wrap-up) progress.md 갱신
