---
name: write-identity
description: Establish what your service stands for — write the Mission, Core Values, Vision, and a first cut of Goals.
metadata:
  version: "2.0.0"
  category: writing
  type: composite
  style: guide
  triggers: [define service identity, write mission statement, establish core values, set up identity, identity setup]
  uses: []
---

# Writing Identity

> Defines the service identity through Mission, Core Values, Vision, and a rough Goals list.
> Run this once before starting any Goal-level work.

## Prerequisites

- Service name and target user known (collected via conversation if not provided)

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **service_name** | N | Service name (collected via conversation if omitted) | task-app |
| **target_user** | N | Target user (collected via conversation if omitted) | freelancers |
| **project_path** | Y | Project workspace root | banas/workspace |
| **year** | Y | Initiative year | 2026 |

## Output

| Step | Output | Path |
|------|--------|------|
| Create | Mission | `{project_path}/identity/mission.md` |
| Create | Core Values | `{project_path}/identity/core-values.md` |
| Create | Vision | `{project_path}/identity/vision_1.md` |
| Create | Goals (rough) | `{project_path}/initiative/{year}/goals.md` |

## Procedure

1. **Collect context**
   - [ ] If `service_name` is not provided, ask: "What is the name of your service?"
   - [ ] If `target_user` is not provided, ask: "Who are the primary users of this service?"
   - [ ] Gather any additional context about the problem domain

2. **Define Mission** — ref: [assets/mission.md](assets/mission.md)
   - [ ] Write a one-sentence mission statement: "For [who], through [how], we build [what]."
   - [ ] Define key terms used in the mission
   - [ ] Write the underlying philosophy (beliefs that support the mission)
   - [ ] Save to `{project_path}/identity/mission.md`

3. **Define Core Values** — ref: [assets/core-values.md](assets/core-values.md)
   - [ ] Define 3–5 core values
   - [ ] For each value, write a decision-making criterion: "When in doubt, ask: [question]"
   - [ ] Save to `{project_path}/identity/core-values.md`

4. **Define Vision** — ref: [assets/vision.md](assets/vision.md)
   - [ ] Describe a concrete future state the service aims to reach
   - [ ] Write measurable achievement conditions (checklist format)
   - [ ] Save to `{project_path}/identity/vision_1.md`

5. **Draft Goals list** — ref: [assets/goals.md](assets/goals.md)
   - [ ] List Goals that contribute to the Vision (rough — will be elaborated later)
   - [ ] Assign IDs: G1, G2, ...
   - [ ] Link each Goal to a core value
   - [ ] Mark each as Feature or Enabler
   - [ ] Save to `{project_path}/initiative/{year}/goals.md`

## Folder Structure

```
{project_path}/
├── identity/
│   ├── mission.md
│   ├── core-values.md
│   └── vision_1.md
└── initiative/{year}/
    └── goals.md
```

## Completion Checklist

- [ ] mission.md created — explains the "why"
- [ ] core-values.md created — 3–5 values with decision criteria
- [ ] vision_1.md created — concrete future state with measurable conditions
- [ ] goals.md created — Goal IDs assigned, linked to values, Feature/Enabler classified
- [ ] Ready to hand off to writing-phase or writing-goal
