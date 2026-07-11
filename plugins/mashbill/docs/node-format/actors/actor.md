---
kind: actor
canvas: actors
field_count: 4
status: draft   # draft → reviewing → done
---

# actor — 액터

> 서비스에 참여하는 사람(역할). master + sub-actor (상속). 정본:
> `viewer/src/domain/Actor.ts`. 상속 로직: `domain/actorInheritance.ts`.

## 1. 고유 필드 — 무엇 + 설계 의도 + 진짜 필요한가

| 필드 | 무엇인가 | 설계 의도 | 진짜 필요/유용한가 |
|---|---|---|---|
| `motivation` | 이 액터가 원하는 것 | 페르소나의 동기 — 설계 출발점(User-Centricity) | ✅ 유용. UX 원칙상 핵심 |
| `pain` | 이 액터의 페인포인트 | 해결할 문제를 노드에 명시 | ✅ 유용. motivation 과 한 쌍 |
| `side` | operator / user / null | 운영자 vs 사용자 구분 (2-plane) | ✅ 구조적으로 필요 (레이아웃·필터) |
| `body` | 자유 서술 | 산문 보강 | ⚠️ motivation+pain 으로 충분하면 잉여 |

## 2. 핵심 질문

- 이 kind 는 비교적 견고 — 4개 필드가 각자 다른 일을 함 (중복 적음).
- `side` 가 `null` 인 경우의 의미가 뭔가? (미정 vs 양쪽 → both 없음에 주의:
  actor_ref 엔 both 없고 actor 도 operator/user/null 만 — service.target_side
  엔 both 있음. **side 값 집합이 kind마다 다른 게 의도된 건가?**)
- 상속(sub-actor)으로 motivation/pain/side/body 가 derived 됨 — 빈 필드가
  "비었다" 인지 "상속받음" 인지 데이터로 구분되나?

## 3. 작업 정의

- [ ] side 값 집합 불일치(actor vs service.target_side vs actor_ref) 의도 확인
- [ ] body 충전율 — 잉여면 제거 검토

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 4: motivation/pain/side/body). |
