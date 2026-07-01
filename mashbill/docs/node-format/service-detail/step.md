---
kind: step
canvas: service-detail
field_count: 4
status: draft   # draft → reviewing → done
---

# step — 스텝 (인터랙션)

> ServiceDetail 흐름의 사용자 액션 1개 (불변식: step = 사용자 액션).
> 정본: `viewer/src/domain/Step.ts`.

## 1. 고유 필드 — 무엇 + 설계 의도 + 진짜 필요한가

| 필드 | 무엇인가 | 설계 의도 | 진짜 필요/유용한가 |
|---|---|---|---|
| `order` | 흐름 내 순서(number\|null) | 순차 정렬 | ❓ 엣지가 순서를 이미 표현 — order 가 엣지와 충돌하면? SSOT 둘 |
| `outcome` | 이 액션 뒤 시스템 결과 (인라인 표시) | "사용자 액션 → 시스템 반응"을 한 노드에 | ✅ 유용 (v0.27.19 핵심) |
| `polarity` | positive/negative/neutral | 네거티브 케이스 시각 구분 (v0.28.2) | ✅ 유용 — 실패 경로 표시 |
| `body` | 자유 서술 | 산문 보강 | ⚠️ 충전율 낮을 듯 |

## 2. 핵심 질문

- **step 의 본체(사용자가 무엇을 하는가)는 `label` 에만 있고** 타입 필드는
  부가(outcome/polarity). 이게 의도된 구조인가? (label 이 사실상 필수 본체)
- `order` vs 엣지 순서 — **둘 다 순서의 SSOT 가 되면 충돌.** 하나로.
  (자동정렬·흐름은 엣지를 따르는데 order 는 왜?)

## 3. 작업 정의

- [ ] order 제거(엣지가 SSOT) vs 유지 결정
- [ ] body 충전율 확인 — 잉여면 제거

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 4: order/outcome/body/polarity). |
