---
kind: rule
canvas: service-detail
created_via: service inspector CompositionList
field_count: 4
status: draft   # draft → reviewing → done
---

# rule — 규칙

> 서비스/흐름의 정책·검증 규칙 (예: "이메일 포맷 체크", 권한 정책). service
> 인스펙터의 CompositionList 로 생성. 정본: `viewer/src/domain/Rule.ts`.

## 1. 고유 필드 — 무엇 + 설계 의도 + 진짜 필요한가

| 필드 | 무엇인가 | 설계 의도 | 진짜 필요/유용한가 |
|---|---|---|---|
| `policy` | 규칙 내용 | 규칙 본체 | ✅ 본체 (있다면) |
| `enforcement` | 어떻게 집행되나 | 규칙의 강제 방식 | ⚠️ policy 와 경계 모호 |
| `actor_permissions` | 액터별 권한 맵 `Record<actor,perm>` | 누가 무엇을 할 수 있나 | ❓ **무거움.** 맵 구조를 실제로 채우나? sim 충전율? |
| `body` | 자유 서술 | 산문 | ⚠️ |

## 2. 핵심 질문

- `actor_permissions` 가 `Record<string,string>` — **유일한 맵 타입 필드.**
  이 복잡한 구조가 실제로 쓰이나? 안 쓰이면 가장 먼저 칠 후보.
- rule 은 어디서 사나? service 인스펙터로 만들지만 ServiceDetail 흐름의
  검증(decision 앞)으로도 등장 가능 — **rule 과 decision 의 경계는?**
  (decision=분기, rule=정책 — 흐름에서 둘이 겹치지 않나)
- sim 에서 rule 이 실제로 쓰였는지부터 확인 (미사용이면 content 와 함께
  존재 정당성 재검토).

## 3. 작업 정의

- [ ] sim 에서 rule 사용 여부 + actor_permissions 충전율 확인
- [ ] rule vs decision 경계 명문화
- [ ] actor_permissions 미사용 시 제거

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 4: policy/enforcement/actor_permissions/body). |
