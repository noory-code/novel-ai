# Novel — System Architecture (Open-Core)

> Canonical (system level). Parent = [`VISION.md`](./VISION.md) (essence/identity). This document = how Novel is
> *composed and deployed* — the plugin / app / engine boundaries and their *intent*. Engine-internal bounded
> contexts = [`specs/domain.md`](./specs/domain.md). Mashbill code shape =
> [`mashbill/docs/ARCHITECTURE.md`](../mashbill/docs/ARCHITECTURE.md) (different altitude). The commercial
> application's product requirements are private and are not part of this public plugin contract.

## Principle — Open-Core

- **The engine and protocol are open** (open-source plugins, MIT). **The product (app) is closed** (proprietary, paid).
- The boundary is drawn **by value**: **the visual canvas experience = the app's sole paid value.** If a plugin
  hands out the canvas, the app's value evaporates → therefore the canvas is **app-only**.

## Three Pieces

| Piece | License | What | Output |
|---|---|---|---|
| **Plugin** (e.g. mashbill · Solera) | Open MIT | **Headless MCP engine** + Claude Code glue (skills/agents/hooks) | **Structured data + text/markdown artifacts.** No UI |
| **App** (Novel app) | Proprietary, paid | **MCP host + visual canvas + composition shell** | A spatially viewable, touchable **canvas experience** |
| **Shared data** | Open format | `.noory/` project files (JSON) | **Both** plugin and app read and write |

- What the app "uses" = each plugin's **engine (MCP server)**. skills/hooks/agents are for the *direct Claude Code
  path*. **The shared core = the engine.**

## Value Boundary (why the canvas = app-only)

- **Plugin artifact = text/markdown** (mission, actors, services as organized prose + publications). The agent reads
  and edits the *meaning*.
- **App artifact = visual canvas** (a spatial, interactive representation of the same data). The human *thinks fast*.
- = VISION's "structure for AI to work on + humans thinking fast" as a **physical division of labor** (AI → structure/plugin,
  human → visual/app, shared = `.noory/`).
- **The moat = not data lock-in** (`.noory/` is open) → **the quality of the visual experience, UX, and composition.**
  Someone can render the open data, but the app's worth must lie in that *experience* (the normal shape of open-core).

## Data Continuity — Frictionless Free→Paid (no lock-in)

- The plugin and the app read/write the **same `.noory/` data** (not "shared" but *identical*). The data lives in
  the user's workspace/repo — **owned by the user**, not on a server.
- **Upgrade path:** work accumulated over N months with the plugin (free) stays as-is in `.noory/`, and on paying
  for the app the app simply *opens that folder* — **no import, no migration, same files.** Concepts/relationships/
  definitions are 100% intact (only the visual *layout* is auto-arranged by the app).
- **Open-core funnel:** accumulate data and habits headlessly for free → pay when you want to *see* it visually →
  zero switching friction because the data is already there. The open data means **no lock-in** = consistent with
  the moat being the *experience*.
- Same for every plugin (Mashbill `.noory/novel/`, Solera `.noory/solera/` — each owns its own data folder).
  Continuity is guaranteed by the plugin engine ↔ app viewer sharing **one schema** through committed generated
  artifacts at the repository boundary.

## Dependency Direction (one-way)

- **App → plugin engine** (the app hosts and consumes the engine). **The engine does not know the app** (headless, independent).
- The plugin **works without the app** (Claude Code + MCP). The app without the engine is an empty shell.
- Forbidden: the engine (plugin) importing app code (R8 — the single forbidden direction).

## Deployment Topology

```
Open-source plugins (MIT) — each = a headless engine (MCP) + Claude Code glue
  • Mashbill plugin → mashbill (canvas/sketch engine)
  • Solera plugin   → solera   (project-workflow engine)
  • …
        │  MCP stdio (에이전트 — agent)  ·  HTTP (앱 viewer — app viewer)   ← 엔진 듀얼 모드, 호스트 무관 (engine dual-mode, host-agnostic)
        ▼
Novel app (proprietary, paid) — MCP host + visual canvas + composition shell
  • viewer (canvas UI)
  • engine hosting: mashbill · solera · … (compiled sidecar bundle)
  • human + AI work together here
        ▲
        │  AI = 외부 에이전트(MCP)  또는  인앱 채팅 — 둘 다 (AI = external agent (MCP) or in-app chat — both)
     user / AI (the external agent coordinates with the app via .noory/ + an optional bridge)
```

## Composition Vision (multi-plugin — later)

- The app hosts several engines (mashbill + solera + …) → one paid product. **The unified canvas/data
  UX = undesigned** (design it then). Because the engines are MCP, plugging them in is itself open — no decision needed now.

## Migration Status

The open-core boundary migration is complete:

- The viewer resides in the separate commercial app repository.
- Mashbill is headless and exposes API/MCP interfaces only.
- Python↔TypeScript wire parity crosses the repository boundary through committed generated artifacts; neither
  repository imports the other by filesystem path.

Decision source = [`mashbill/docs/DECISIONS.md`](../mashbill/docs/DECISIONS.md) `D-2026-06-20-A`.
Source-repository relocation guidance = [`MIGRATION.md`](./MIGRATION.md).
