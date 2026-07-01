---
kind: identity
canvas: foundation
field_count_before: 4   # description, do, dont, body
field_count_after: 4    # description, body + status(enum) + provenance(string[]); evolution deferred
status: done   # draft → reviewing → done — v0.44.0 (D-2026-06-07-A)
---

# identity — 아이덴티티

> **개념(정본): [`concepts/kinds.md`](../../../../../docs/concepts/kinds.md).** (옛 FOUNDATION_CONCEPT 흡수.)
> 아이덴티티 = **쌓여가는 지향. 어떤 존재이고 싶은가** (미래/지향).
> **★ 입력이 아니라 출력** — AI 가 미션+코어밸류(+누적 설계/행동)에서
> 도출하고 계속 갱신. 필드 정본: `viewer/src/domain/Identity.ts`.

## 출력값 렌즈 — 이게 핵심 (2026-06-06)

미션·코어밸류는 **입력**(인터뷰로 받음)이라 "사람이 어느 필드를 채우나"가
질문이었다. **아이덴티티는 출력**이라 그 질문이 바뀐다 — "AI 가 무엇을
도출·누적하고, 그걸 어떻게 추적·진화시키나."

> ⚠️ **현실 caveat:** 현재 BANAS 14개 identity 는 *손으로 작성*된 것
> (AI 도출은 아직 미구현). 아래는 **출력값 모델의 목표 설계** + 손작성으로도
> 동작하는 graceful degradation.

### 3개 열린 질문, 출력 렌즈로 재판정

| # | 1차 비판 | 출력 렌즈 재판정 |
|---|---|---|
| ① body 이중산문 | description+body 중복 | **컷 유지.** 출력의 도출 내용은 단일 prose 면 충분 → `description` 하나 |
| ② facet/14-flat | 시스템 잃은 노드가방? | **격하 → "예정된 보류".** 출력이 *쌓이므로* facet 분류는 누적 출력을 정리/재사용하는 데 쓸모가 커짐. deliverable 이 facet 묶음을 요구할 때 도입 |
| ③ catch-all | 안티패턴·감정여정이 identity 맞나? | **해소.** *도출된* "되고 싶은 존재"는 본디 보이스·비주얼·감정·부정공간을 넘나든다. 안티패턴=도출된 *부정 공간*, 감정여정=도출된 *감정 아크*. 이질성은 결함이 아니라 누적 출력의 본성 |

### 출력이라서 새로 필요한 구조 (목표 모델)

입력 kind 엔 없던, **출력이라 정당화되는 구조 필드들** (산문 아님 →
structural-vs-prose 원칙상 자리값 있음):

- **provenance (도출 출처)** — 이 identity 가 *어느 미션/코어밸류/서비스
  설계에서* 도출됐나. 추적성 = 신뢰("AI 가 왜 이게 우리라고 하나") + 사용자
  확인/교정의 근거. 출력의 핵심.
- **evolution (진화 이력)** — "쌓여가는" → 언제 어떻게 갱신됐나. BaseFields.
  version 보다 풍부한 변경 추적이 identity 에선 중심 (출력이 계속 진화).
- **status (도출/확정)** — AI 도출 초안인지 사용자가 확인·고정했는지.
  입력 kind 엔 없는 구분.

### 채우는 방식 — 인터뷰가 아니라 도출→확인 (2026-06-06)

미션·코어밸류는 AI 가 **질문해서** 채우는 입력이지만, identity 는 **출력**이라
방향이 반대다:

- AI 가 미션+코어밸류(+누적 설계)를 읽고 **identity 초안을 도출**해 노드에
  채운다 (사용자한테 "당신의 정체성은?"이라 묻지 않는다 — 그건 출력을 입력처럼
  다루는 오류).
- 사용자의 몫은 **확인·교정**: "여기 도출된 결이 맞나요? 고칠 부분은?"
  (= status: 도출 → 확정). 이게 identity 의 "인터뷰" 등가물.
- 캔버스 AI 대화창에서: 미션·코어밸류 인터뷰가 끝나면 AI 가 identity 를 제안,
  사용자가 대화로 다듬음.

### Graceful degradation
AI 도출이 약하거나 미구현이어도 identity 는 **손작성으로 동작**해야 한다:
label + description (현재 14개가 그러함). provenance/evolution/status 는
*AI 도출이 붙을 때의 향상 레이어* — 단계적 구현.

## 데이터 근거 (현재 14개, 손작성)
| 필드 | 충전율 |
|---|---|
| `description` | 14/14 |
| `do` / `dont` / `body` | 0/14 |

노드당 `description` 하나만 사용 (do/dont 컷 배치 대상, body 중복 컷).

## 자기비판 (self red-team)
- **YAGNI 우려:** provenance/evolution/status 는 *미구현* AI 도출을 위한
  설계 — 이르지 않나? 반박: 사용자가 "아이덴티티=출력"을 Novel 의 핵심
  차별점으로 명시 → 목표 모델 정의는 정당, *구현은 단계적*.
- **출력 모델이 희망사항일 위험:** AI 도출이 실전에서 약하면 identity 는
  손작성(현재)로 회귀 → 그래서 graceful degradation 을 못박음.
- ②facet/③catch-all 을 "출력이라 자연스럽다"로 너무 쉽게 풀었나? — facet 은
  *예정된 보류*로 남겨 증거(누적량/deliverable 수요) 나올 때 재검토하도록 함.

## 파운데이션 3종 종합
| kind | 입출력 | 콘텐츠 | 추가 구조 |
|---|---|---|---|
| mission | 입력 | label + body | — |
| core_value | 입력 | label + definition (+body) | — |
| identity | **출력** | label + description | **provenance · evolution · status** (목표) |

→ 입력 2종은 label+단일 prose 로 수렴. **출력 1종(identity)만 구조가 다르다**
— 그게 본질(입력 vs 출력)의 차이를 정확히 반영.

## 작업 정의
- [x] (확정) do/dont/body 컷 → content = `description` (+ body). v0.43.2.
- [x] (구현) provenance — `string[]` 도출 출처 노드 id. v0.44.0 (D-2026-06-07-A).
- [x] (구현) status(manual/derived/confirmed) 플래그. v0.44.0 (D-2026-06-07-A).
- [ ] (보류) evolution 추적 — git+version 중복 + writer 부재. AI 도출 writer 착륙 시 재개.
- [ ] (보류) facet 분류 — deliverable 의 facet 묶음 수요 발생 시.
- [x] (못박음) graceful degradation — 손작성(label+description, status=manual, provenance=[])만으로 동작.

## 검토 히스토리

> 검토는 반복된다. 매 검토마다 시각 + 바뀐 것을 changelog 로 남긴다.

| 검토 | 시각 (KST) | 결과 / 바뀐 것 |
|---|---|---|
| 생성 | 2026-06-04 23:19 | draft 생성 (필드 4: description/do/dont/body). |
| 1차 | 2026-06-05 03:24 | 검토 — description 14/14, do/dont/body 0/14. |
| 2차 | 2026-06-05 03:40 | "그대로 두자"로 잠정 done. |
| 3차 | 2026-06-05 03:46 | **비판으로 재오픈** — body 이중산문/14flat/catch-all. |
| 4차 | 2026-06-06 | **출력값 렌즈 재정의.** ①body컷 ②facet 예정보류 ③catch-all 해소. 출력이라 provenance·evolution·status 구조 추가(목표 모델, 단계 구현). graceful degradation 못박음. |
| 5차 | 2026-06-06 | 채우는 방식 명시 — 인터뷰(입력) 아니라 **AI 도출→사용자 확인·교정**(출력). identity 의 "인터뷰 등가물"은 확인 단계. |
| 6차 | 2026-06-06 | **do/dont 컷 구현 (v0.43.2).** identity = description + body. 옛 do/dont → body 로 fold. 출력모델(provenance/evolution/status)·facet 은 여전히 미래 TARGET. |
| 7차 | 2026-06-07 | **출력모델 구현 (v0.44.0, D-2026-06-07-A).** `status`(manual/derived/confirmed, default manual) + `provenance`(string[]) 를 구조 필드로 추가 (canvas.json only, MD split 아님). **evolution 보류** — git+version 중복 + writer 부재 (YAGNI). graceful degradation: 손작성 manual 로 계속 동작. node-format **done**. |
