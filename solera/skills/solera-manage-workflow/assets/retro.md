# Template: Retrospective (v3)

Retrospectives are written at **Story Wrap-up** and (optionally) **Release cut** — the two points where 결과 확정 happens.

## Perspective

| Level | Perspective | Location |
|-------|-------------|----------|
| **Story** | AI behavior — how AI decomposed, implemented, handed off | `stories/{story}/RETROSPECTIVE.md` |
| **Release** | Project retrospective — what this Release represents, what was cut, what's next | `releases/{tag}/README.md` (covers retro content too) |

v3 does **not** use Phase / Goal / Epic retrospectives (those items were removed). Business retrospectives happen at Milestone / Release boundaries through `solera-release`'s README step.

## Story RETROSPECTIVE.md — AI Behavior

```markdown
# Retrospective: {story_id}-{story_name}

> Completed: {YYYY-MM-DD}
> Contributed to: {concept_id_1}, {concept_id_2}

## Summary

| Item | Details |
|------|---------|
| **Objective** | {original User Story / Technical Goal} |
| **Result** | {actual result — what was produced} |

## AI Did Well

- {effective decisions or execution}

## AI Did Poorly

- {mistakes, inefficiencies, drift from Concept intent}

## AI Improvements

- {specific behaviors AI should change in the next Story}

## Instruction System Issues

- {omissions / ambiguities / errors in skills, rules, templates}

## Concept Contribution Summary

<!-- Required. One block per Concept in contributes_to. -->

### {concept_name}

**What this Story left behind**: {1–2 sentences, grounded in Output Artifacts}

**Proposed Current Shape update**: {AI draft revision}

**Approved Current Shape**: {what the human approved}

**Drift note**: {optional — if Story drifted from Intent or Current Design}
```

## Quality Criteria

- [ ] Written from the correct perspective (AI behavior for Story)
- [ ] Every section has at least one item (use "(none)" only if truly empty)
- [ ] Improvements are actionable for the next Story
- [ ] Concept Contribution Summary present for every `contributes_to` entry
- [ ] Drift notes flagged where applicable
