---
kind: content
canvas: service-detail
created_via: service inspector CompositionList
field_count: 4
status: draft   # draft → reviewing → done
---

# content — 콘텐츠

> 서비스에서 생산/소비되는 콘텐츠 (예: 게시물, 메시지). producer/consumer
> 액터를 가짐. service 인스펙터 CompositionList 로 생성. 정본:
> `viewer/src/domain/Content.ts`.

## 1. 고유 필드 — 무엇 + 설계 의도 + 진짜 필요한가

| 필드 | 무엇인가 | 설계 의도 | 진짜 필요/유용한가 |
|---|---|---|---|
| `format` | 콘텐츠 형식 (텍스트/이미지 …) | 콘텐츠 종류 명시 | ❓ 쓰이나? |
| `producer_actor_id` | 생산자 액터 | 누가 만드나 | ⚠️ 액터-콘텐츠 관계를 엣지 아닌 필드로 — 일관성? |
| `consumer_actor_id` | 소비자 액터 | 누가 소비하나 | ⚠️ 위와 동일 |
| `body` | 자유 서술 | 산문 | ⚠️ |

## 2. 핵심 질문

- **존재 정당성:** sim(BANAS) 에서 content 노드가 실제로 쓰였나? 1차 판정은
  "미사용 의심". 안 쓰였으면 YAGNI 위반 — 만들어두고 안 쓰는 kind.
- producer/consumer 를 **필드(id)** 로 들고 있음 — 다른 kind 의 관계는 엣지로
  그리는데(All edges are user-drawn) content 만 필드로 액터를 가리킴. **관계
  표현 방식 불일치** (엣지 vs id 필드).
- content 가 "콘텐츠 자체"인지 "콘텐츠 흐름의 한 노드"인지 — actor_ref 의
  gives/receives 로도 표현 가능한 것 아닌가 (중복).

## 3. 작업 정의

- [ ] sim 에서 content 사용 여부 확인 (미사용이면 제거 1순위)
- [ ] producer/consumer 를 엣지로 돌릴지 (관계 표현 일관성)
- [ ] rule 과 함께 "service 인스펙터 생성 kind" 의 존재 가치 재검토

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 4: format/producer_actor_id/consumer_actor_id/body). |
