# mashbill 엔진 — 코드-도메인 맵 (구현 거처)

> **개념 정본은 root** — [`docs/specs/domain.md`](../../../docs/specs/domain.md) (`D-2026-06-28-B`).
> 바운디드 컨텍스트의 *의미·경계·의존 방향·entity vs value-object·공유 용어*는 거기 있다(오픈
> 엔진과 상용 앱이 공유하는 모델). 이 파일은 그 모델을 **엔진 코드에 어떻게 박았나** — 컨텍스트별
> 코드 거처, 코드 레벨 용어 매핑, 코드-도메인 갭 — 만 둔다.
>
> **코드 어디 둘지 판단할 때:** ① root `specs/domain.md`에서 페이즈→컨텍스트를 먼저 짚고
> ② 여기서 그 컨텍스트의 코드 거처를 본다 ③ 거기 있는 파일에 더하거나, 없으면 그 컨텍스트
> 디렉터리에 새 파일을 만든다 ④ 금지 import(root 규칙)를 피한다.

---

## 컨텍스트별 코드 거처 (current)

5개 컨텍스트 정의는 root. 각각이 *지금* 코드에서 사는 곳:

| 컨텍스트 | 코드 거처 (current) |
|---|---|
| **EssenceDiscovery** | `mashbill/foundation/` · `mashbill/templates/foundation/` · (뷰어) Foundation 인스펙터 섹션 |
| **EssenceRetention** | `mashbill/projects/anchors.py` · (뷰어) `sketch/useNodesMemo.ts`(앵커 주입) · `sketch/applyAnchorChange.ts` |
| **EssencePlanning** | `mashbill/canvases/actors/` · `mashbill/canvases/services/` · (뷰어) `sketch/autoLayout.ts` · `sketch/useEdgesMemo.ts` |
| **EssenceExecution** | `mashbill/canvases/service_detail/` · `mashbill/server.py`(MCP 도구 등록) · (뷰어) `sketch/SketchModals.tsx`(드릴 모달) |
| **AICollaboration** | `mashbill/skills/` · `mashbill/agents/` · `mashbill/hooks/` · `mashbill/.claude-plugin/plugin.json` · `mashbill/server.py`(도구 표면) |

> 뷰어 코드(`viewer/src/…`)는 컷(D-2026-06-20-M) 후 상용 앱 레포 `plot/viewer/`에 산다 —
> 여기 경로는 *어느 컨텍스트의 표면인지*를 가리키는 표기일 뿐, 엔진 레포 안 링크가 아니다.

## 코드 레벨 용어 (root 공유 용어의 코드 매핑)

root의 공유 용어를 엔진 코드 타입에 맺는 구분. (개념 정의는 root `specs/domain.md` §핵심 용어.)

| 용어 | 코드 매핑 | 구분 |
|---|---|---|
| **Node** | `CanvasDoc.nodes[]`의 `SketchNode` | DOM 노드도, `ReactFlow.Node`도 아님 |
| **rf-node** | React Flow 런타임 표현(`{id, position, data}`) | `SketchNode`와 별개. `useNodesMemo`가 둘을 잇는 경계 |
| **Anchor** | `PROJECT_ANCHOR_ID`(`__project_anchor__`)로 식별, `useNodesMemo`가 주입 | `canvas.json`에 저장 안 됨; 위치는 `ProjectDoc.anchors` |
| **Edge** | `CanvasDoc.edges[]`의 `SketchEdge` | 런타임 `rf-edge`와 별개 |

## 현재 코드-도메인 맵 (갭 리스트)

코드가 모델을 어기는 자리. 각 행은 비용·이득 있는 리팩터 후보(우선순위 = `ARCHITECTURE.md`).
⚠ 일부 행은 stale일 수 있음 — 갭 감사는 별도 작업.

| 어디 | 관심사 | 지금 사는 곳 | 있어야 할 곳 | 심각도 |
|---|---|---|---|---|
| 앵커 렌더 | EssenceRetention | `sketch/useNodesMemo.ts`(일반 노드 변환과 섞임) | EssenceRetention(자체 모듈) | 중 — 동작은 함; 분리하면 명료 |
| 오토레이아웃 알고리즘 | EssencePlanning | `sketch/autoLayout.ts` | EssencePlanning ✓ | 없음 — 이미 맞음 |
| 커서 SSOT | 가로지름(시각 계약) | `styles.css` + `CURSOR.md` | 그대로 OK — 시각 계약엔 자연스런 도메인 거처 없음 | 없음 |
| MCP 도구 등록 | Execution + AICollaboration | `mashbill/server.py` | OK — 도구 표면이 곧 경계 | 없음 |
| Service-Detail 모달 | EssenceExecution | `sketch/SketchModals.tsx` | EssenceExecution ✓ | 낮음 |

## 이 파일이 바뀔 때

- 컨텍스트의 코드 거처가 옮겨지거나(빈번; bookkeeping) 갭 리스트가 늘고 준다.
- 컨텍스트 자체의 *정의*가 바뀌면 → root `specs/domain.md` + `D-YYYY-MM-DD-X`(이 파일 아님).
- 의존 방향 다이어그램·공유 용어의 *개념*은 root가 SSOT — 여기서 중복하지 않는다.
