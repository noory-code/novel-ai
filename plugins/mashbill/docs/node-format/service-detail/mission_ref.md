---
kind: mission_ref
canvas: service-detail
field_count: 2
status: draft   # draft → reviewing → done
---

# mission_ref — 미션 참조

> Foundation 의 mission 을 흐름에 *주입(발동)* 하는 포인터. "이 서비스가
> 어떤 미션에 답하나". 정본: `viewer/src/domain/MissionRef.ts`.

## 1. 고유 필드 — 무엇 + 설계 의도 + 진짜 필요한가

| 필드 | 무엇인가 | 설계 의도 | 진짜 필요/유용한가 |
|---|---|---|---|
| `ref_mission_id` | 가리키는 master mission id | 참조 링크 | ✅ 필수 |
| `notes_in_context` | 이 맥락에서의 메모 | 발동 지점 설명 | ⚠️ 충전율? 빈칸이면 순수 포인터 |

## 2. 핵심 질문 (★ 3 ref 통합 — 가장 큰 횡단 질문)

- **mission_ref / value_ref / identity_ref 의 구조가 100% 동일**
  (`ref_<x>_id` + `notes_in_context`). 차이는 가리키는 대상 kind 뿐.
  → **하나의 `foundation_ref` { ref_kind, ref_id, notes_in_context } 로
  합칠 수 있나?** kind 3개 → 1개. (반대 근거: 색/스텐실 섹션이 kind별로
  갈려서 시각 구분에 쓰임 — 그건 ref_kind 로도 가능.)
- 합치면 16 kinds → 14 kinds. no-god-object 원칙과 충돌하지 않음
  (discriminated 가 아니라 동일 구조의 통합).

## 3. 작업 정의

- [ ] 3 foundation ref 를 단일 foundation_ref 로 통합할지 결정 (★)
- [ ] notes_in_context 충전율 확인

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 2: ref_mission_id/notes_in_context). |
