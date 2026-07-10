---
kind: service
canvas: services
field_count: 10
status: draft   # draft → reviewing → done
---

# service — 서비스

> 한 목적의 사용자 인터랙션 단위 (로그인/온보딩/프로필편집 …). 카테고리
> 안의 leaf. **고유 필드 10개로 가장 무겁다 — 과적합 위험 최대.** 정본:
> `viewer/src/domain/Service.ts`.

## 1. 고유 필드 — 무엇 + 설계 의도 + 진짜 필요한가

| 필드 | 무엇인가 | 설계 의도 | 진짜 필요/유용한가 |
|---|---|---|---|
| `what` | 이 서비스가 무엇인가 | 본체 정의 | ✅ 필수 |
| `value_created` | 이 서비스가 만드는 가치 | 산출 가치 명시 (Q6 산출물 직결) | ✅ 중요 — but metric 과 중복(아래) |
| `scope` | 범위/경계 | 서비스 경계를 못 박으려고 | ⚠️ what 과 경계 모호 |
| `trigger` | 무엇이 이 서비스를 시작시키나 | 진입점 명시 | ⚠️ ServiceDetail 의 첫 step 과 중복 |
| `how` | 어떻게 동작하나 | 동작 개요 | ⚠️ ServiceDetail 전체가 "how" 임 → 중복 |
| `outcome` | 끝났을 때 결과 | 종료 상태 | ⚠️ ServiceDetail 의 result step / value_created 와 중복 |
| `do` | 권장 | 실천 경계(+) | ⚠️ core_value/identity 와 공유 — 서비스에도 필요? |
| `dont` | 비권장 | 실천 경계(−) | ⚠️ 위와 동일 |
| `body` | 자유 서술 | 산문 | ⚠️ 위 9개가 이미 광범위 → body 남는 게 있나 |
| `target_side` | operator/user/both/null | 대상 면 | ✅ 구조적 (필터/레이아웃). but actor/actor_ref 와 값 집합 다름 |

## 2. 핵심 질문 (이 kind 가 감사 핵심)

- **10개 중 절반이 ServiceDetail 과 중복.** `trigger`(첫 step) /
  `how`(흐름 전체) / `outcome`(result step) 은 ServiceDetail 캔버스가 이미
  표현함. **서비스 노드에 같은 걸 또 텍스트로 둘 이유가 있나?** —
  ServiceDetail 있으면 요약만, 없으면 텍스트 폴백?
- `value_created` vs `metric` 노드 — 둘 다 "만드는 가치". 하나로?
- `what` vs `scope` 경계, `do`/`dont` 의 서비스 적용성.
- → **service 는 10개에서 대폭 줄일 1순위 후보.**

## 3. 작업 정의

- [ ] sim 11개 service 의 10개 필드 충전율 표로 뽑기 (어느 게 늘 비나)
- [ ] trigger/how/outcome 을 ServiceDetail 파생으로 돌릴지 결정
- [ ] value_created ↔ metric 관계 정리 (Q6 와 함께)
- [ ] do/dont 3-kind 공통 결정에 포함

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 10 (최대)). |
