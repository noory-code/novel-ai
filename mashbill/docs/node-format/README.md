# node-format/ — 노드 종류(kind)별 데이터 형식 감사

> ⚠ **kind 필드 정본 = [`../../../../docs/specs/kinds-fields.md`](../../../../docs/specs/kinds-fields.md)**
> (root). 이 폴더는 마라톤 전 *감사 기록*(SSOT 아님 — 무엇이 왜 있고 유용한가를 따진 이력).

> **노드 종류 1개 = 문서 1개.** 각 문서는 그 kind가 가진 프로퍼티 +
> **설계 의도**(여러 세션에 걸쳐 만들어진 것) + **"이게 진짜 있어야 하나 /
> 정말 유용한가"** 심문을 담는다. 사용자(검토자)가 각 항목을 도전해서
> **불필요한 필드를 쳐내고 정당한 필드 셋을 확정**한다.
>
> **목적:** Novel 노드 데이터 모델을 kind 단위로 감사 → 발행/산출물(Q6)을
> 올리기 전에 형식을 의도적으로 다시 정한다.
>
> **개념 정본:** [`../../../../docs/concepts/kinds.md`](../../../../docs/concepts/kinds.md) —
> 미션(뿌리/입력)→코어밸류(현재/입력)→아이덴티티(지향/**출력**). 파운데이션
> kind 의 *형식*은 이 *개념*에서 따라 나온다. 형식 감사 전에 개념을 본다.
> (옛 FOUNDATION_CONCEPT → concepts/ai-collaboration·kinds 로 흡수.)
>
> 이 폴더의 결론은 `../CONCEPTS.md`(코드-near 정본) + root `docs/specs/kinds-fields.md`
> 로 올라간다. (옛 상위 계획 NODE_DATA_AND_ARTIFACTS_PLAN 폐기.)
>
> **필드 정본(SSOT):** `plot/viewer/src/domain/<Kind>.ts`
> (서버 Pydantic ↔ TS 패리티: `mashbill/tests/test_schema_parity.py`).
> 이 문서는 SSOT 가 아니라 *무엇이 왜 있고 유용한가* 를 따지는 감사 기록.

## 폴더 구조 — 캔버스 단위

각 kind는 **스텐실에 등장하는 캔버스**로 묶는다 (정본:
`viewer/src/canvases/SketchStencil.tsx`).

```
node-format/
├── README.md
├── foundation/      ← 파운데이션 캔버스
│   ├── mission.md
│   ├── core_value.md
│   └── identity.md
├── actors/          ← 액터 캔버스
│   └── actor.md
├── services/        ← 서비스 캔버스
│   ├── category.md
│   └── service.md
└── service-detail/  ← 서비스 디테일 캔버스 (흐름 + 본질 주입)
    ├── actor_ref.md      (서비스 캔버스에도 등장 — multi-canvas)
    ├── step.md
    ├── decision.md
    ├── metric.md
    ├── mission_ref.md
    ├── value_ref.md
    ├── identity_ref.md
    ├── group.md
    ├── rule.md          (service 인스펙터 CompositionList 로 생성)
    └── content.md       (service 인스펙터 CompositionList 로 생성)
```

| kind | 문서 | 고유 필드 | 1차 판정 |
|---|---|---|---|
| mission | [foundation/mission.md](foundation/mission.md) | 4 | direction 의심 |
| core_value | [foundation/core_value.md](foundation/core_value.md) | 4 | do/dont 충전율 |
| identity | [foundation/identity.md](foundation/identity.md) | 4 | core_value 와 형식 동일 |
| actor | [actors/actor.md](actors/actor.md) | 4 | 비교적 견고 |
| category | [services/category.md](services/category.md) | 2 | theme 의심 |
| service | [services/service.md](services/service.md) | 10 | 과적합 위험 최대 |
| actor_ref | [service-detail/actor_ref.md](service-detail/actor_ref.md) | 4 | gives/receives = 가치 |
| step | [service-detail/step.md](service-detail/step.md) | 4 | 본체가 label뿐? |
| decision | [service-detail/decision.md](service-detail/decision.md) | 1 | body 만 — 분기조건 필드? |
| metric | [service-detail/metric.md](service-detail/metric.md) | 3 | service.value_created 와 중복 |
| mission_ref | [service-detail/mission_ref.md](service-detail/mission_ref.md) | 2 | 3 ref 통합 후보 |
| value_ref | [service-detail/value_ref.md](service-detail/value_ref.md) | 2 | 3 ref 통합 후보 |
| identity_ref | [service-detail/identity_ref.md](service-detail/identity_ref.md) | 2 | 3 ref 통합 후보 |
| group | [service-detail/group.md](service-detail/group.md) | 2 | member_ids vs RF parent |
| rule | [service-detail/rule.md](service-detail/rule.md) | 4 | actor_permissions 무거움 |
| content | [service-detail/content.md](service-detail/content.md) | 4 | sim 미사용 — 존재 정당성 |

## 검토 규칙 (review history)

각 kind 문서는 끝에 **`## 검토 히스토리`** 표를 갖는다. 검토는 한 번이
아니라 **반복**된다 — 매 검토마다 한 행을 추가한다.

```
| 검토 | 시각 (KST)        | 결과 / 바뀐 것 |
|------|-------------------|----------------|
| 생성 | YYYY-MM-DD HH:MM  | draft 생성 (필드 N: …). |
| 1차  | YYYY-MM-DD HH:MM  | **검토 완료.** <무엇이 바뀜>. status → done. |
| 2차  | …                 | <재검토에서 바뀐 것> |
```

- **시각은 추측하지 않는다** — 실제 시각(`date`) 또는 커밋 시각(`git log`)을 쓴다.
- frontmatter `status`(draft→reviewing→done)는 *현재 상태*, 히스토리 표는
  *변경 이력*(changelog). 둘 다 유지.
- "검토 완료"는 그 회차 행에 굵게 표시 + status 갱신.

## 공통 필드 (BaseFields — 모든 kind 공유, 각 문서에서 반복 안 함)

`id`, `label`, `x`, `y`, `width`, `height`, `color`, `shape`, `icon`,
`collapsed`, `is_root`, `details_path`, `owner`, `version`,
`publish_baseline`.

- **label** — 모든 노드의 표시 이름. 다수 kind에서 *본체*가 label에만 있고
  타입 필드는 부가인 경우 많음 (step/decision 특히) — 심문 대상.
- **details_path** — 외부 상세 문서 포인터. sim 전부 `null` = **미사용**.
  공통 열린 질문: 살릴지 죽일지 (PLAN G3/G5).
- **version / publish_baseline** — per-node 버저닝/발행 baseline. 내용
  형식과 직교(별도 축) — 형식 감사에서 제외.
- **color / shape / icon** — 시각 속성. 데이터 의미 아님.

## 횡단 패턴 (kind 사이에서 반복 — 별도 주목)

- **`body`** — 12 kind 공유 자유 markdown. 형식 합의 필요(PLAN Q1/Q2).
  각 문서는 "이 kind에서 body가 타입필드와 겹치나"만 본다.
- **`do` / `dont`** — core_value·identity·service 3 kind 공유. 같은 의미인가?
- **`*_ref` + `notes_in_context`** — mission_ref·value_ref·identity_ref
  구조 동일. 하나로 합칠 수 있나(가장 큰 횡단 질문).
- **"가치"의 중복** — service.`value_created` · metric · actor_ref.`gives`
  /`receives` 가 모두 "교환/산출되는 가치". Q6 산출물과 직결.
