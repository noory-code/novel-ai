---
kind: core_value
canvas: foundation
field_count_before: 4   # definition, do, dont, body
field_count_after: 2    # label (name) + body — definition folded (D-2026-06-16-M)
status: done   # draft → reviewing → done
decided: 2026-06-04
---

# core_value — 코어밸류

> **개념(정본): [`concepts/kinds.md`](../../../../../docs/concepts/kinds.md).** (옛 FOUNDATION_CONCEPT 흡수.)
> 코어밸류 = **현재의 노력. 지금 어떻게 결정하는가** (현재/노력). 사용자에게
> **인터뷰로 받는 입력**. 필드 정본: `viewer/src/domain/CoreValue.ts`.

> **⚠ 현재 필드 (D-2026-06-16-M, 코드 반영 D-2026-07-02-A):** `label`(가치 이름) +
> `body`(의미 + 트레이드오프) **두 칸.** `definition` 은 제거됨 — 이름과 definition 이
> 같은 원칙을 두 번 말하던 중복이라 접었고, definition 은 읽을 때 `body` 선두 문단으로
> 흡수된다(무손실). 아래 2026-06-04~06 본문은 `definition + body` 로 정한 **당시 기록**
> (definition 컷 이전) — 역사로 보존. 최신 결론은 이 배너 + root `concepts/kinds.md`.

## 개념 (2026-06-05 프레임) — 결론 확인

코어밸류 = "지금 무엇을 어떻게 결정하는가"(현재/입력). BANAS: **관용과 지지**
— 뉴비 환영, 실수에 너그럽고, 노력을 응원한다.

이 프레임은 기존 결론을 **확인**한다 (뒤집지 않음): 데이터에서 `do` 5/5 가
"판단 기준: ~인가?"로 쓰인 게 우연이 아니라 **코어밸류의 본질(=의사결정
기준)** 그 자체였다. 즉 definition 이 곧 "어떻게 결정하는가"의 진술 →
do(판단기준)는 그 재진술이라 컷, definition + body 유지. 변경 없음.

## 결정 (사용자 확정 2026-06-04)

**코어밸류 = `definition` + `body`. `do`·`dont` 폐기.**

```
core_value
├── label       ← 가치 이름 (관용 / 지지 …)
├── definition  ← 가치 원칙 한 문장  [유지]
└── body        ← 선택적 부연 (자유 markdown)

✗ do   ✗ dont        ← 폐기
```

- 코어밸류 = "그 집단이 타협하지 않는 하나의 **선택 원칙**" (결정의
  갈림길에서 어느 쪽으로 기울지 정해주는 기준). 그 원칙은 `definition`
  한 문장이면 선다.
- **`do` 컷:** 데이터상 `do` 5/5 가 전부 "판단 기준: ~인가?" — 즉
  `definition` 을 의문문으로 바꾼 *같은 원칙의 재진술*. 별도 데이터가 아님
  (과분해). 잘 선 원칙은 "무엇을 할지"를 함의한다.
- **`dont` 컷:** 0/5. 사람은 긍정 원칙은 쓰되 부정형은 안 쓴다(비대칭).

### body 내용 — 인터뷰로 유도 (2026-06-06)

코어밸류는 **입력**(인터뷰). 채우는 방식 = 캔버스 AI 대화창이 질문해 대화로
채움 (FOUNDATION_CONCEPT). 지금은 정적 프롬프트, 나중엔 AI 챗이 같은 질문
재사용.

- **코어밸류 = 이 프로젝트에서 결정할 때 *우선시되어야 하는 가치*** (결정이
  어려울 때만이 아니라, 모든 의사결정에서 우선하는 가치). (사용자 정의 2026-06-06)
- **인터뷰 질문(초안):** "이 프로젝트에서 **결정할 때 우선시되어야 하는
  가치**는 무엇인가요?"
- `definition` = 그 답(우선 가치 한 문장). `body` = 선택적 부연 — 비어도 됨.

**다운스트림 — 서비스 기획에 적용 (핵심):** 코어밸류는 정의하고 끝이 아니라
**서비스를 기획할 때 모든 결정에 적용**되어야 한다 (사용자 2026-06-06: "서비스를
기획할 때 이게 다 쓰여야 한다"). 서비스 설계의 갈림길마다 *우선 가치*로
작동하며, 그 적용은 ServiceDetail 의 `value_ref` 주입(발동)으로 가시화된다
(Q6 "체현"과 직결). → 파운데이션은 입력 후 잠드는 게 아니라 흐름 전반의 렌즈.

## do/dont 일반 결론 (3 kind 공통)

`do`/`dont` 는 core_value·identity·service 가 공유하는 필드다. 위 논리는
세 곳 모두에 적용된다 — **필드로서는 불필요.** 단, "아닌 것(부정 공간)"의
*가치 자체* 는 있다 (identity 의 `안티패턴` 노드가 증거). 그러나 그건
**모든 노드에 강제된 `dont` 필드** 가 아니라, 진짜 중요할 때 **body 또는
독립 노드** 로 쓴다. → do/dont 필드는 3 kind 에서 일괄 컷.

## 근거 — 실제 BANAS 데이터 (5개 core_value)

| 필드 | 충전율 | 실제 쓰임 |
|---|---|---|
| `definition` | **5/5** | 가치 원칙 + 인라인 `[Be All]`/`[New All]` 태그 |
| `do` | **5/5** | "판단 기준: ~인가?" = definition 의 의문문형 (재진술) |
| `dont` | **0/5** | 죽은 필드 |
| `body` | **0/5** | 비어 있으나 선택적 부연 슬롯으로 유지 |

예: 유머 → definition "웃음이 벽을 깬다" / do "사람들을 웃게 하는가?" (동일).

## 경영학 근거

- **Lencioni, *Make Your Values Mean Something*** (HBR 2002): 가치는
  의사결정을 이끌 때만 의미. "판단 기준"이 그 operationalization 이지만,
  그건 가치(definition) 그 자체이지 별도 필드가 아니다.
- **Collins & Porras**: core value = 소수의 시대불변 원칙, 외부 정당화
  불필요 → 무거운 do/dont 다필드는 가치 본성과 안 맞음.

## 자기비판 (self red-team)

- 직전 초안의 "definition+criteria 2개 구조는 살아있다"는 **틀렸다.**
  definition 과 do 는 같은 원칙의 평서/의문 두 형태 — 과분해였다.
- n=5 가 한 작성자라 일반화 주의했으나, do=definition 재진술 + dont 0/5 는
  논리(가치=원칙)와도 일치해 컷 근거가 충분.

## 횡단 메모

- `[Be All]`/`[New All]` 태그가 definition 안 인라인 — 분류 축으로 쓸 거면
  별도 태그 후보 (지금은 자유 텍스트, 보류).

## 작업 정의

- [ ] `do`, `dont` 제거 (definition 재진술 / 0/5)
- [ ] do/dont 일괄 컷을 identity·service 감사에 적용
- [ ] domain/CoreValue.ts + Pydantic + 인스펙터/렌더러 + schema_parity
- [ ] `[Be All]/[New All]` 분류 필드화 여부는 나중 결정

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 4: definition/do/dont/body). |
| 1차 | 2026-06-05 02:34 | **검토 완료.** do(=definition 재진술)·dont(0/5) 컷 → definition + body. status → done. |
| 2차 | 2026-06-06 | 개념 프레임 반영 — 코어밸류=현재/지금 어떻게 결정하는가/입력. "판단 기준"이 본질임을 개념이 확인. 결론 변경 없음. |
| 3차 | 2026-06-06 | body 유도 = 인터뷰 질문 추가("무엇을 기준으로 정하나요?"). definition=답, body=선택 부연. |
| 4차 | 2026-06-06 | 정의 교정 — 코어밸류 = 결정 시 *우선시되는 가치*(어려울 때만 ✗). 질문 교체. 다운스트림: 서비스 기획 전 결정에 적용(value_ref 발동). |
