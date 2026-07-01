# Novel — NEXT SESSION queue

> **Surfaced automatically by the SessionStart hook
> (`mashbill/hooks/session_start.py`) at every new session start.**
> When the user invokes a queued item by its trigger keyword, that
> item becomes the active task for the session.
>
> **일감 SSOT = [`noory-workspace/todo/`](../../../todo/index.md)** (성격별
> active/verify/discuss/strategy/backlog/shipping). 이 파일은 트리거 키워드로
> 호출되는 *세션 진입점*만 남긴다 — 세부 일감 목록은 `todo/`에서 관리한다.
> 완료된 항목은 줄을 지운다(취소선으로 쌓지 않음 — 이력은 git·DECISIONS).

---

## Active queue

### `AI 채팅 코치 — 캔버스별 토론` (★ TOP — filed 2026-06-17, updated 2026-06-18)

> **Trigger:** user says **"AI 채팅"** / **"채팅 토론"** / **"플레이북"** /
> **"코치"** / **"큰그림"** / **"이어가자"** / **"다음"** as the first / near-first message.
>
> **⚠ 다음에 이어갈 것 = 토론이다 (구현 아님).** (사용자 지시 2026-06-18.)
>
> **먼저 읽기:** [`../../../docs/concepts/ai-collaboration.md`](../../../docs/concepts/ai-collaboration.md)
> — 채팅 구조 + 캔버스별 코치 인터뷰 정본 (옛 AI_CHAT_PLAYBOOK 흡수). 결정 원문 =
> [`DECISIONS.md`](./DECISIONS.md) `D-2026-06-16-H`~`D-2026-06-19-F`.
>
> **토론 순서:** Foundation → Actors → Services → 기능(Feature). (Entities = 가로지름.)
>
> **남은 토론 안건:** A) 주경로 = 인터뷰먼저 vs 외부에이전트(충돌) · B) 스레드 keying
> service vs feature · C) 컨텍스트 봉투 주경로 도달 · D) 적극 코치 *내용* · E) Entities 코치 신뢰성.
>
> **⚠ 코드 *구현* 선행 블로커:** kind-count drift 정합. 단 플레이북 *내용 토론*은 추상
> seam(`D-2026-06-17-L`)에만 의존해 **지금 가능**. 세부 일감 = `todo/`.

### `노드 데이터 형식 + 산출물 관리` (filed 2026-06-04; foundation 3종 DONE)

> **Trigger:** user says **"노드 데이터"** / **"문서 형식"** / **"산출물"** /
> **"버저닝"** / **"발행 정리"** / **"이어서"** / **"다음"** as the first /
> near-first message.
>
> **개념 정본 먼저 읽기:** [`../../../docs/concepts/kinds.md`](../../../docs/concepts/kinds.md)
> (미션=뿌리/입력, 코어밸류=현재/입력, 아이덴티티=지향/**출력**) + kind별 감사
> [`node-format/`](./node-format/).
>
> **남은 항목 (foundation 3종은 완료):**
> 1. **인터뷰 질문 → 캔버스 AI 대화창** — kind별 인터뷰 질문 세트(정의됨)를 정적 body
>    프롬프트로 깔지 / AI 챗에 붙일지.
> 2. **나머지 kind 감사** — actors / services(10필드, 감축 1순위) / feature
>    (3 ref 통합, "가치" 3중복 등). `node-format/` 참조.
> 3. **산출물(deliverable, Q6)** — 서비스 "가치 시트" 번들러.
>
> **⚠️ 2026-06 대대적 개편이 위 잔여 항목보다 우선일 수 있음 — 새 세션 첫 메시지로
> 개편 범위를 확인할 것.** 세부 일감 = `todo/`.

### `BANAS 시뮬레이션 이어가기` (filed 2026-06-01)

> **Trigger:** user says **"바나스"** / **"BANAS"** / **"시뮬"** /
> **"마인드맵 정렬"** / **"그룹 노드"** as the first / near-first message.
>
> 사용자가 **real BANAS blueprint**를 Novel에 채우며 깨지는 것을 고친다. 전체 상태 +
> 설계 = **[`BANAS_SIM_BACKLOG.md`](./BANAS_SIM_BACKLOG.md)** (먼저 읽기).
>
> **다음 할 두 작업 (백로그에 상세):**
> 1. **Mindmap-quality tree layout** — 새 `computeMindmapLayout` (재귀 parent-relative
>    radial tree, disjoint subtree sectors): 노드 겹침·엣지 교차 없음. 사용자 승인 방향.
> 2. **Foundation group hubs** (핵심 가치 / 아이덴티티; mission stays direct)
>    — **model change 블로커**: Foundation 캔버스가 `{mission,core_value,identity,project}`
>    만 허용(422 gate). grouping kind 허용 vs 새 foundation-group kind 결정 후 채우기.
>
> **Live env:** sim project at `/Users/woogis/Workspace/banas-sim/banas` (project id `banas`).
> Launch: `cd mashbill && uv run mashbill-http` (:5190) + `cd plot/viewer && npm run dev` (:5193),
> open `http://localhost:5193/?project_path=/Users/woogis/Workspace/banas-sim/banas&project=banas`.
> **Gotcha:** restart the MCP server after pulling server-side changes.

### `Service composition model — follow-ups` (filed 2026-05-28)

> **Trigger:** user says **"서비스 정의"** / **"service model"** /
> **"step graph"** / **"actor anchor"** / **"admin drop"** as the first / near-first message.
>
> Service composition model은 SPEC + DECISIONS(`D-2026-05-28-J`)에 pin됨 + 레이아웃
> 알고리즘 재작성(actor-anchored, direction adaptive). 아래는 그 세션에서 남은 작은
> 독립 스레드들 — 사용자가 먼저 말하는 것으로 고른다.

**Open follow-ups (각각 작은 독립 ship):**

1. **Admin actor_ref silent drop bug** *(filed inside D-2026-05-28-K notes;
   user-visible 422 is gone but the drop itself is open).* reload-then-⊞ 사이클에서
   프런트 PUT body가 operator-side `actor_ref`를 떨어뜨림(백엔드 doc엔 있음).
   2-actor → 1-actor invariant 완화로 422는 사라졌지만 데이터 drop은 남음 — silent loss.
   Live demo: `plot-test-v013/.plot/banas-imported/services/n_mpkyhvsj_mjzh`.
   접근: `useNodesMemo` + `useAutoLayout` `onDocChange` 파이프라인 instrument →
   `getCanvas`와 다음 `putCanvas` 사이 어디서 `actor_ref`가 필터되는지 찾기.
2. **Auto-seed update.** `sync_details_with_overview`가 아직 `actor_ref` 둘
   (`{sid}-operator-ref` + `{sid}-user-ref`)을 seed. `D-2026-05-28-J`상 operator
   side는 서비스 자체라, 기본 seed는 user-side 하나여야. UX call: back-compat로 둘 다
   둘지, 하나 seed하고 사용자가 operator 추가하게 할지.
3. **Bigger design questions raised mid-session but not closed:**
   - **Actor 계층 명시화** — Bana → Hero / Fan as mode-specialisations. 현재 implicit;
     Actor 캔버스에 parent edge 없음. 공간 표현 열림.
   - **Multi-actor services.** `D-2026-05-28-J`는 subject가 sequence를 따라 inherit
     한다고 함 — 실제 두 번째 human role(P2P payer + payee 등)은 subject edge 둘 이상
     필요. 현재 `actorAnchoredLayout`는 첫 subject edge 이후를 무시. "실제 케이스
     만나면" follow-up.

**Live test doc:** `plot-test-v013/.plot/banas-imported/services/n_mpkyhvsj_mjzh/detail.json`
holds the user-confirmed Login graph — reload + ⊞ on this doc is the smoke test for any
layout change. **Ground rules:** SPEC.md §"Service composition model" (`D-2026-05-28-J`)
for what every ServiceDetail must contain; DECISIONS `D-2026-05-28-J` for the rejected
alternatives.

---

### `Research subject 백데이터 기능` (queued, lower priority, filed 2026-05-19)

> **Trigger:** user says **"인터뷰 데이터"** / **"리서치 서브젝트"** /
> **"interview subjects"** / **"research subjects"** / **"백데이터"** as
> the first / near-first message.
>
> **Decision (D-2026-05-19-A):** Actor 캔버스 stays role-level (4-layer max).
> Research subjects live in the actor's `body` Markdown field under a `## 인터뷰 대상자`
> section. No new typed fields, no new kind, no new canvas. YAGNI.
>
> **Trigger to revisit:** User starts tracking 10+ research subjects per actor, or the
> body MD becomes unwieldy. When that pain accumulates, evaluate:
>
> | Option | Cost | Boundary impact |
> |---|---|---|
> | `body` MD section (current) | 0 | 0 |
> | `subjects: SubjectEntry[]` new typed field | Pydantic + TS + Inspector | low |
> | New "Research" canvas | high (4 → 5 canvases) | medium |
> | External tool link (Notion etc.) | 0 | 0 (separation clean) |
>
> Most likely path: row 1 or row 4 — promote to row 2 only when usage demands.

---

### `Foundation 정리 + Actor 정리` (queued, filed 2026-05-18)

> **Trigger:** user says **"foundation 정리"** / **"파운데이션 정리"** /
> **"actor 정리"** / **"액터 정리"** / **"banas foundation"** /
> **"banas actor"** as the first / near-first message.
>
> **Scope (open — re-anchor with user at session start):**
>
> Foundation pass — likely candidates:
> - banas-imported의 Mission / Core Values / Identity 컨텐츠 정돈 (typed-text 필드 다시
>   살펴, body 정리, edge 그리기로 관계 표현).
> - 추가 identity 노드 (visual identity / brand voice) 후보.
> - Foundation 캔버스의 anchor 위치 + 노드 placement 손볼 수도.
>
> Actors pass — likely candidates:
> - Hero / Fan / Bana 페르소나의 sub-actor 추가 (vertical specialisation).
> - Actor 간 관계 edge (Hero ↔ Fan: 양방향 지지).
> - Bana = Hero + Fan 의 union 이라는 의미를 시각적으로 표현 (parent_id 또는 edge 로).
>
> **Novel 의 본질 기준 — 공간 기반만 다루기. 시간 / 단계 / 마일스톤 류는 안 들임.**
> **Approach:** plan-mode 짧게 + AskUserQuestion 으로 lock (시각자료 활용).

---

### `MCP-driven node creation via AI conversation` (queued, filed 2026-05-17)

> **Trigger:** user says **"MCP 대화"** or **"AI 로 노드 만들기"** or
> **"context_envelope"** or **"conversation MCP"**.
>
> **Filed:** 2026-05-17 (user explicit deferral). Combines with tree-in-forest
> [D-2026-05-16-D](./DECISIONS.md) Layer 2 (`context_envelope` MCP tool).
>
> **Scope sketch (plan-mode required):**
> - New / extended MCP tools: `context_envelope(node_id)`, `draft_node_proposal`,
>   `apply_node_proposal`.
> - Conversation pattern: AI walks user through node creation, pulls context
>   (parent ancestors + sibling identity / mission refs), drafts typed fields,
>   calls `update_canvas` to materialize.
>
> **Approach:** plan-mode + mashbill-design-red-team. Substantial phase — own design
> discussion + likely 2-3 ships.

---

### `cross-kind ref typed-text symmetry` (lower priority, filed 2026-05-16)

> **Trigger:** user says **"ref symmetry"** or **"ref typed text"** or
> **"actor_ref vs mission_ref"** or **"ref 비대칭"**.
>
> **Filed:** 2026-05-16 (D-2026-05-16-F follow-up). actor_ref 만 `gives` / `receives`
> 라는 ref-context-specific typed text 를 가지는데, mission_ref / value_ref /
> identity_ref 는 pure pointer. 의도적 비대칭인지(actor 만 *행동 단위*), 4 ref 모델이
> 통일되어야 하는지 미해결.
>
> **Approach:** 별도 plan-mode — 4 ref 의도 비교 / 사용 사례 발견 시 typed text 추가 검토.
> ⚠ feature(옛 service_detail) 캔버스에서 ref 종류 다수 폐기됨(`D-2026-06-17-B/H`)
> — 재논의 전 그 결정 먼저 반영.

---

### `v0.22.x follow-up — publish-button placement + size` (lower priority, filed 2026-05-17)

> **Trigger:** user says **"publish 버튼 크게"** or **"인스펙터 아래 publish"** or
> **"footer publish"** as the first / near-first message.
>
> **Scope (proposal — re-anchor with user before implementing):**
> - Move the 📤 publish button from the BaseInspector header to a **sticky footer
>   inside the Inspector aside**, full-width, taller, primary CTA styling.
> - Keep the dirty-gate from D-2026-05-17-H.
> - Sticky positioning so the footer stays visible regardless of scroll.
>
> **Ship as:** v0.22.x patch (UX-only). Requires mashbill-design-red-team pass.

---

### `v0.18.x follow-up — Unpublish button` (lower priority)

> **Trigger:** user says **"Unpublish"** or **"미스클릭"** or
> **"publish 취소"** as the first / near-first message.
>
> **Filed:** 2026-05-16. Phase 3 ships without an Unpublish button (recovery is manual
> via `git revert HEAD` + optional MD-file rm, per [`PUBLISH.md`](./PUBLISH.md)). Once
> real usage shows the misclick rate, automate.
>
> **Scope:**
> - Inspector header: **↩ unpublish** button next to **📤 publish**, visible only when
>   `node.version != "v1.0"`.
> - Server endpoint
>   `POST /api/projects/{id}/canvases/{kind}/nodes/{node_id}/unpublish` — find most
>   recent publish commit (`git log --grep "^Publish-Node-Id: {node_id}"`),
>   `git revert <sha> --no-edit`, `rm` the published MD file the revert left behind.
> - Confirmation dialog naming the version rollback explicitly.
> - Tests: unit-test the revert flow against the fake-repo fixture.
>
> **Ship as:** v0.18.x patch once the misclick rate justifies it.

---

## Roadmap items (queued but lower priority)

The remaining big-scope work is filed in
[`ROADMAP.md` §"v0.17+ — Roadmap items"](./ROADMAP.md), with the
`mashbill-design-red-team` 8-attack findings baked into each item:

- **A) isomorphic-git source-data version control** — spec-mandated; 6 Major findings
  need `DECISIONS.md` answers before any code.
- **B) Work-item layer (userstory + task)** — spec-mandated; hard dependency on A;
  4 Major findings.
- **C) Novel repository split** — product decision the user owns.
- **D) Forest-anchored AI context (graph-RAG-lite + verification loop)** — Phase 1
  pinned by `D-2026-06-17-L`; no hard dependency on A/B/C.

Pick order on the next session: invoke one of the trigger phrases `isomorphic-git` /
`git 통합` / `일감 레이어` / `work-item` / `repo split` / `레포 분리` / `forest context` —
and the session re-enters plan mode against the ROADMAP entry's findings as the anchor.

---

## How this file works

- The `SessionStart` hook (`mashbill/hooks/session_start.py`) reads this file at every
  session start and prepends each `### TRIGGER` heading to the assistant's context.
- The assistant then watches for the user's next message. If it contains a trigger
  keyword, the assistant executes the matching item.
- **완료 항목은 줄을 지운다** (취소선·아카이브로 쌓지 않음 — 이력은 git·CHANGELOG·DECISIONS).
- 세부 일감은 [`noory-workspace/todo/`](../../../todo/index.md)가 SSOT. 이 파일은 트리거
  진입점만 유지한다.
