# Mermaid Authoring Rules: Service Map

> Mermaid diagram rules used in Service Map documents

## Mindmap (structure/hierarchy)

```mermaid
mindmap
  root((central topic))
    branch1
      sub1
      sub2
    branch2
```

| Syntax | Shape | Purpose |
|--------|-------|---------|
| `((text))` | Circle | Root node |
| `text` | Default | General node |
| `(text)` | Rounded rectangle | Emphasis node |
| `[text]` | Rectangle | Separator node |

> Use 2-space indentation to denote hierarchy levels

## Flowchart (flow/relationships)

```mermaid
flowchart LR
    A[feature1] -->|relationship| B[feature2]
    B --> C[result]

    classDef planned fill:#f5f5f5,stroke:#999,color:#666
    classDef v1 fill:#c8e6c9,stroke:#4caf50
```

| Color | classDef | Meaning |
|-------|----------|---------|
| Gray | `planned` | Not implemented |
| Green | `v1` | Implemented in v1.x |
| Blue | `v2` | Implemented in v2.x |

## Version/Status Notation

Display status in flowchart, and **also manage in a table**.

```markdown
| Feature | Description | Status | Version |
|---------|-------------|--------|---------|
| **feature1** | description | not implemented | - |
| **feature2** | description | implemented | v1.0 |
```

> mindmap = **structural overview**, flowchart = **flow/status expression**, table = **detailed information**

---

## Example: BANAS

### Structure (mindmap)

```mermaid
mindmap
  root((BANAS))
    Platform
      Profile
      Social
      Content
      Club
      Salon
      Town
      Reputation
    Vertical
      Bartender
        Liquor Info
        Partner
    Admin
      User Management
      Content Management
      Data Management
```

### Flow (flowchart)

```mermaid
flowchart TB
    ALBA[ALBA] -->|profile management| PROFILE[Profile]
    ALBA -->|club operations| CLUB[Club]
    BANA[BANA] -->|follow| SOCIAL[Social]
    BANA -->|join club| CLUB
    SOCIAL --> REPUTATION[Reputation]
    CLUB --> REPUTATION

    classDef planned fill:#f5f5f5,stroke:#999,color:#666
```

### BANAS Service Map Folder Structure

```
catalog/service-map/
├── index.md                    # BANAS overall picture
├── admin/                      # Admin
│   └── index.md                # Management point index
├── platform/                   # Platform common
│   ├── profile.md              # Profile
│   ├── social.md               # Follow/likes
│   ├── content.md              # Content
│   ├── club.md                 # Club
│   ├── salon.md                # Salon
│   ├── town.md                 # Town
│   └── reputation.md           # Reputation
└── vertical/                   # Vertical-specific
    └── bartender/
        ├── index.md            # Bartender vertical overview
        ├── liquor.md           # Liquor info
        └── partner.md          # Partner
```
