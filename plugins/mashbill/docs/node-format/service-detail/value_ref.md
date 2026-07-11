---
kind: value_ref
canvas: service-detail
field_count: 2
status: draft   # draft → reviewing → done
---

# value_ref — 코어밸류 참조

> Foundation 의 core_value 를 흐름에 *주입(발동)* 하는 포인터. "이 서비스가
> 어떤 가치를 체현하나". 정본: `viewer/src/domain/ValueRef.ts`.

## 1. 고유 필드 — 무엇 + 설계 의도 + 진짜 필요한가

| 필드 | 무엇인가 | 설계 의도 | 진짜 필요/유용한가 |
|---|---|---|---|
| `ref_value_id` | 가리키는 master core_value id | 참조 링크 | ✅ 필수 |
| `notes_in_context` | 이 맥락에서의 메모 | 발동 지점 설명 | ⚠️ 충전율? |

## 2. 핵심 질문

- **mission_ref / value_ref / identity_ref 구조 동일** →
  단일 `foundation_ref` 로 통합 후보. 상세 논의는
  [mission_ref.md](mission_ref.md) §2 (★) 참조.
- value_ref(체현) vs metric/value_created(산출) — "가치"가 또 등장.
  체현되는 가치(value_ref) ≠ 산출되는 가치(metric)? 이 구분이 데이터로
  명확한가 (Q6 체현 vs 산출).

## 3. 작업 정의

- [ ] 3 foundation ref 통합 결정에 포함 (★ mission_ref §2)
- [ ] 체현(value_ref) vs 산출(metric) 가치 구분 명문화

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 2: ref_value_id/notes_in_context). |
