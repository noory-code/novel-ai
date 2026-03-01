# Template: Retrospective (회고)

계층 완료 시 RETRO.md를 작성한다.

## 회고 유형

| 계층 | 관점 | 핵심 질문 |
|------|------|----------|
| **Phase** | 비즈니스 | 분기 목표 달성? ROI? 다음 분기 전략? |
| **Goal** | 비즈니스 | 사용자 가치 달성? Epic 간 우선순위 적절? |
| **Epic** | AI 행동 | AI가 잘한 점? 못한 점? 개선점? 인스트럭션 문제? |
| **Story** | AI 행동 | AI가 잘한 점? 못한 점? 개선점? 인스트럭션 문제? |
| **Action Item** | AI 행동 | AI가 잘한 점? 못한 점? 개선점? 인스트럭션 문제? |

## RETRO.md — AI 행동 회고 (Epic / Story / Action Item)

```markdown
# 회고: [Epic/Story/ACT명]

> 완료일: [YYYY-MM-DD]

## 요약

| 항목 | 내용 |
|------|------|
| **목표** | [원래 목표] |
| **결과** | [실제 결과] |

## AI 잘한 점

- [AI가 효과적으로 수행한 작업/판단]

## AI 못한 점

- [AI가 실수/비효율/오판한 부분]

## AI 개선점

- [다음 작업에서 AI가 바꿔야 할 행동]

## 인스트럭션 시스템 이슈

- [스킬/룰/워크플로우에서 발견된 문제점]
- [템플릿, 절차, 산출물 정의의 개선 사항]
```

## RETRO.md — 비즈니스 회고 (Phase / Goal)

```markdown
# 회고: [Phase/Goal명]

> 완료일: [YYYY-MM-DD]

## 요약

| 항목 | 내용 |
|------|------|
| **계획** | [원래 계획] |
| **결과** | [실제 결과] |
| **소요** | [예상 vs 실제] |

## 잘한 점 (Keep)

- [유지할 점]

## 개선할 점 (Problem)

- [문제점]

## 시도할 점 (Try)

- [다음에 시도할 점]

## 배운 점 (Learned)

- [교훈]
```

## 회고 위치

| 계층 | 위치 |
|------|------|
| **Phase** | `workspace/phase/{phase_id}/RETRO.md` |
| **Goal** | `workspace/phase/{phase_id}/goals/{goal_id}/RETRO.md` |
| **Epic** | `workspace/phase/.../epics/{epic_name}/RETRO.md` |
| **Story** | `workspace/phase/.../stories/{story_id}/RETRO.md` |

## 품질 기준

- [ ] 적절한 관점(AI 행동 vs 비즈니스)으로 작성했는가?
- [ ] 각 섹션이 1개 이상 항목을 포함하는가?
- [ ] 개선점이 다음 작업에 적용 가능한가?
