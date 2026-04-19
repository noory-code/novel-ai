---
name: solera-write-identity
user-invocable: true
description: Establish what your service stands for — write the Mission, Core Values, Vision, and an optional rough list of direction candidates that feed the first Concepts.
metadata:
  version: "3.0.0"
  category: writing
  type: unit
  style: guide
  triggers: [define service identity, write mission statement, establish core values, set up identity, identity setup]
  uses: []
---

# Writing Identity (v3)

> Defines the service identity through Mission, Core Values, Vision, and an optional rough-directions list.
> Run this once before drawing your first Concept.

In v3, the output of this skill is **all on the Living axis** — it never creates v2-era `initiative/` or Phase/Goal hierarchies. The optional "rough directions" list from Step 5 is a human jotting-pad that feeds into the next step (`solera-write-concept`), not a structured work item.

## Prerequisites

- Service name and target user known (collected via conversation if not provided).

## Input

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| **service_name** | N | Service name (collected via conversation if omitted) | task-app |
| **target_user** | N | Target user (collected via conversation if omitted) | freelancers |
| **project_path** | Y | Project workspace root | banas |

## Output

| Step | Output | Path |
|------|--------|------|
| Create | Mission | `{project_path}/.solera/identity/mission.md` |
| Create | Core Values | `{project_path}/.solera/identity/core-values.md` |
| Create | Vision | `{project_path}/.solera/identity/vision_1.md` |
| Create (optional) | Rough directions | `{project_path}/.solera/identity/rough-directions.md` |

## Procedure

1. **Discovery Interview**
   - [ ] If `team-process.md` exists at `{project_path}/.solera/team-process.md`, read it and skip questions already answered
   - [ ] If `service_name` is not provided, ask: "What is the name of your service?"
   - [ ] If `target_user` is not provided, ask: "Who are the primary users of this service?"
   - [ ] Gather persona details for each user type via the following questions.
     Ask all questions per persona; if the answer is vague, ask a follow-up to get specifics.

   **Per-persona interview (NN/G 6-field model):**
   Ask in the user's language. Fields to collect:
   ```
   1. Role — "What is this user's role or occupation?" (e.g. barista, freelance developer, small business owner)
   2. Skill level — "How tech-savvy are they?" (beginner / intermediate / expert)
      → If vague: "Can they install a smartphone app on their own, or are they a developer-level user?"
   3. Usage context — "When, where, and why do they use this service?"
      → e.g. "On mobile during commute, to quickly check inventory"
   4. Primary goal — "What is their ultimate goal when using this service?"
   5. Biggest pain point — "What is their biggest frustration or problem right now?"
   6. Representative quote — "What would this person typically say?" (one sentence)
      → e.g. "I waste 30 minutes every morning just figuring out my inventory."
   ```

   - [ ] Repeat for each persona (2–4 recommended)
   - [ ] **Personas are additive** — when a new user type is discovered later, re-invoke `solera-write-identity` to add a persona without modifying existing ones

2. **Define Mission** — ref: [assets/mission.md](assets/mission.md)
   - [ ] Write a one-sentence mission statement: "For [who], through [how], we build [what]."
   - [ ] Define key terms used in the mission
   - [ ] Write the underlying philosophy (beliefs that support the mission)
   - [ ] Save to `{project_path}/.solera/identity/mission.md`

3. **Define Core Values** — ref: [assets/core-values.md](assets/core-values.md)
   - [ ] Define 3–5 core values
   - [ ] For each value, write a decision-making criterion: "When in doubt, ask: [question]"
   - [ ] Save to `{project_path}/.solera/identity/core-values.md`

4. **Define Vision** — ref: [assets/vision.md](assets/vision.md)
   - [ ] Describe a concrete future state the service aims to reach
   - [ ] Write measurable achievement conditions (checklist format)
   - [ ] Save to `{project_path}/.solera/identity/vision_1.md`

5. **Draft rough directions (optional)** — ref: [assets/goals.md](assets/goals.md)
   - [ ] Ask the human: "Would you like to jot down rough directions you want this service to go? These are not commitments — they become candidates for the first Concepts you draw."
   - [ ] If yes: collect a short bulleted list, linked to core values where relevant.
   - [ ] Save to `{project_path}/.solera/identity/rough-directions.md`.
   - [ ] If no: skip — directions will emerge as you draw Concepts.

## Folder Structure

```
{project_path}/.solera/
└── identity/
    ├── mission.md
    ├── core-values.md
    ├── vision_1.md
    └── rough-directions.md       # optional
```

## Error Handling

| Failure point | Condition | Recovery procedure | Exit behavior |
|---------------|-----------|-------------------|---------------|
| service_name missing | Parameter not provided | Ask user: "What is the name of your service?" | Collect parameter, then continue |
| target_user missing | Parameter not provided | Ask user: "Who are the primary users?" | Collect parameter, then continue |
| project_path missing | Directory does not exist | Run `mkdir -p {project_path}` | Create directory, then continue |
| File write failure | Permission error or disk full | Display error, ask user to check permissions | Skill halted, return error state |
| Template asset missing | Template file not found in assets/ | Generate document with default structure (skip template) | Show warning, continue |

## Completion Checklist

- [ ] mission.md created — explains the "why"
- [ ] core-values.md created — 3–5 values with decision criteria
- [ ] vision_1.md created — concrete future state with measurable conditions
- [ ] (Optional) rough-directions.md created — candidate seeds for the first Concepts
- [ ] Ready to hand off to solera-write-concept (draw the first Concept of the project map)
