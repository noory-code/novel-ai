# Artifact flow — a temporary sketch

> For temporary discussion. Once agreed, pin it into `storage-publish.md` + a `DECISIONS.md` `D-` entry and delete this file.
> Written: 2026-06-21 session. prep = [`artifact-management-prep.md`](./artifact-management-prep.md).

## Lifecycle (loop)

```mermaid
flowchart TD
    Draw["① Draw<br/>draw the node onto the graph<br/>AI reads from here on · no version"]
    Pub["② Publish<br/>stamp a version v1.0→v2.0<br/>+ extract MD + git commit"]
    Make["③ Make<br/>the external agent reads the design<br/>and produces code·implementation"]
    Back["④ Come back<br/>the made result returns to the graph,<br/>attaching an edge (line) to that feature"]

    Draw --> Pub
    Pub --> Make
    Make --> Back
    Back -->|"revisit: discover the missing essence"| Draw

    D1{{"Open 1<br/>how much to bundle when publishing?<br/>a single node vs a whole service"}}
    D2{{"Open 2 ⚠ the weakest link<br/>must it come back with an edge attached?<br/>enforced = the trace never breaks"}}
    D3{{"Open 3<br/>what about big chunks?<br/>whole vs summary+link"}}

    D1 -.-> Pub
    D2 -.-> Back
    D3 -.-> Back

    style D1 fill:#fff3cd,stroke:#d39e00
    style D2 fill:#f8d7da,stroke:#c82333
    style D3 fill:#fff3cd,stroke:#d39e00
```

## The two faces of an artifact

```mermaid
flowchart LR
    Graph["living graph<br/>(JSON SSOT)"] -->|"always on"| AI["AI reads and works"]
    Graph -->|"only when Publish is pressed"| Frozen["frozen publication<br/>(MD + version + git)"]
    Frozen -->|"v2.0 design"| Human["the human points at it"]
```

## Three things to decide (the dotted lines in the chart above)

| # | Fork | Where | Note |
|---|---|---|---|
| 1 | Publish depth — node vs container | ② Publish | directly tied to prep open 2 |
| 2 | Return invariant — enforce the edge? | ④ Come back | **the weakest link** · prep open 5 |
| 3 | Big chunk — whole vs summary+link | ④ Come back | prep open 4 · premised on big projects |
