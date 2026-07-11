---
kind: actor_ref
canvas: service-detail
also_on: services
field_count: 4
status: draft   # draft → reviewing → done
---

# actor_ref — 액터 참조

> Actor 캔버스의 master actor 를 다른 캔버스(service / service-detail)에
> 가리키는 포인터 + 이 맥락에서의 가치 교환. 정본:
> `viewer/src/domain/ActorRef.ts`.

## 1. 고유 필드 — 무엇 + 설계 의도 + 진짜 필요한가

| 필드 | 무엇인가 | 설계 의도 | 진짜 필요/유용한가 |
|---|---|---|---|
| `ref_actor_id` | 가리키는 master actor id | 참조 링크 | ✅ 필수 (ref 의 본질) |
| `gives` | 이 맥락에서 액터가 주는 것 | 관계론적 가치 흐름 (PHILOSOPHY) | ✅ 가치 교환 표현 — but "가치" 중복군 |
| `receives` | 이 맥락에서 받는 것 | 위와 한 쌍 | ✅ |
| `side` | operator/user/null | 면 구분 | ⚠️ master actor 에 이미 side 있음 → 참조면 상속 못 하나? 중복 입력 |

## 2. 핵심 질문

- `side` 가 master actor 에도 있고 actor_ref 에도 있음 — **참조인데 왜 다시
  입력?** master 에서 상속하면 되지 않나 (foundation ref 들은 notes 만 가짐).
- `gives`/`receives` = 가치 교환 → service.value_created, metric 과 같은
  "가치" 군. Q6 산출물 정의에서 가치 표현 SSOT 를 정해야 정리됨.
- ref 4개 kind(actor_ref + 3 foundation ref) 중 actor_ref 만 필드가 많음
  (gives/receives/side). 일관성: ref 는 "참조 + 맥락노트" 만 둘지, actor_ref
  처럼 맥락 데이터를 둘지.

## 3. 작업 정의

- [ ] side 를 master 에서 상속(필드 제거) vs 유지
- [ ] gives/receives 를 "가치 SSOT" 결정에 포함

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 4: ref_actor_id/gives/receives/side). |
