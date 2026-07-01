---
kind: identity_ref
canvas: service-detail
field_count: 2
status: draft   # draft → reviewing → done
---

# identity_ref — 아이덴티티 참조

> Foundation 의 identity 를 흐름에 *주입(발동)* 하는 포인터. "이 지점의
> 톤앤매너/정체성". 정본: `viewer/src/domain/IdentityRef.ts`.

## 1. 고유 필드 — 무엇 + 설계 의도 + 진짜 필요한가

| 필드 | 무엇인가 | 설계 의도 | 진짜 필요/유용한가 |
|---|---|---|---|
| `ref_identity_id` | 가리키는 master identity id | 참조 링크 | ✅ 필수 |
| `notes_in_context` | 이 맥락에서의 메모 | 발동 지점 설명 (예: "입력 카피의 결") | ⚠️ 충전율? |

## 2. 핵심 질문

- **mission_ref / value_ref / identity_ref 구조 동일** →
  단일 `foundation_ref` 통합 후보. 상세는 [mission_ref.md](mission_ref.md) §2 (★).
- identity_ref 는 사용자가 말한 "톤앤매너 발동"의 그릇 (2026-05-30 의도).
  발동을 "보여주는" 데 `notes_in_context` 하나로 충분한가, 아니면 발동
  지점(어느 step 에)·강도 같은 게 필요한가?

## 3. 작업 정의

- [ ] 3 foundation ref 통합 결정에 포함 (★ mission_ref §2)
- [ ] 발동 표현에 notes 외 필드가 필요한지 (Q6 체현/발동)

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 2: ref_identity_id/notes_in_context). |
