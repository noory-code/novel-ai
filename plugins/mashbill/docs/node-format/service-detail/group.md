---
kind: group
canvas: service-detail
field_count: 2
status: draft   # draft → reviewing → done
---

# group — 그룹 (서브플로우)

> ServiceDetail 의 sub-flow 묶음 (예: "이메일 검증" 단계 묶음). collapse 가능.
> 정본: `viewer/src/domain/Group.ts`. 생성: `sketch/groupActions.ts`.

## 1. 고유 필드 — 무엇 + 설계 의도 + 진짜 필요한가

| 필드 | 무엇인가 | 설계 의도 | 진짜 필요/유용한가 |
|---|---|---|---|
| `member_ids` | 묶인 노드 id 배열 | 어떤 노드들이 이 그룹에 속하나 | ⚠️ RF parentNode 와 SSOT 경쟁 (아래) |
| `body` | 자유 서술 | 그룹 설명 | ⚠️ 충전율 낮을 듯 |

## 2. 핵심 질문

- **`member_ids`(명시 배열) vs RF parentNode(트리 부모)** — 멤버십의 SSOT 가
  둘로 갈릴 위험. 현재 group 은 collapse-only(v0.29.0)고 진짜 시각 containment
  (parentNode)은 deferred. 멤버십을 member_ids 로 들지, parent 로 들지 하나로.
- group 은 "데이터" 인가 "뷰 상태(접기)" 인가? collapse 만이면 시각 도구지
  도메인 엔티티가 아닐 수 있음 → kind 일 필요가 있나?

## 3. 작업 정의

- [ ] member_ids vs RF parent 멤버십 SSOT 결정
- [ ] group 이 도메인 kind 여야 하는지 (vs 순수 뷰 그룹) 재검토

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 2: member_ids/body). |
