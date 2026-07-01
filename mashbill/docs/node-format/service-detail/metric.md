---
kind: metric
canvas: service-detail
field_count: 3
status: draft   # draft → reviewing → done
---

# metric — 가치 (VALUES)

> ServiceDetail 에서 인터랙션을 통해 *교환되는* 가치(인스턴스). 정본:
> `viewer/src/domain/Metric.ts`.

## 1. 고유 필드 — 무엇 + 설계 의도 + 진짜 필요한가

| 필드 | 무엇인가 | 설계 의도 | 진짜 필요/유용한가 |
|---|---|---|---|
| `target` | 목표값/대상 | 가치의 지향점 | ⚠️ "metric=측정지표" 와 "가치=value" 가 한 kind 에 섞임 |
| `measurement` | 어떻게 측정하나 | 정량화 방법 | ❓ 사용자 모델은 "교환되는 가치"인데 measurement 는 KPI 냄새 — 미스매치 |
| `body` | 자유 서술 | 산문 | ⚠️ |

## 2. 핵심 질문

- **이름(metric)과 쓰임(VALUES=교환 가치)이 어긋남.** kind 이름은
  metric(지표)인데 스텐실 라벨·사용자 모델은 "가치". `target`/`measurement`
  는 지표(KPI) 필드인데 실제로는 "이 인터랙션에서 무슨 가치가 오가나"를
  적는 데 쓰임 → **필드가 쓰임과 안 맞음.**
- **service.`value_created` 와 중복.** 서비스 레벨 산출가치(value_created)
  vs 인터랙션 레벨 교환가치(metric) — 둘의 관계 정의 필요 (Q6 산출물 직결).
- actor_ref.`gives`/`receives` 도 "가치 교환" — 가치 표현이 3곳에 흩어짐.

## 3. 작업 정의

- [ ] metric kind 를 "value/가치" 로 재정의할지 (이름/필드 정합)
- [ ] value_created ↔ metric ↔ gives/receives "가치 3중복" 정리 (Q6 와 함께)

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 3: target/measurement/body). |
