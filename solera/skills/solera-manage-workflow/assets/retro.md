# Template: Retrospective

Write a RETROSPECTIVE.md when a hierarchy level is complete.

## Retrospective Types

| Hierarchy | Perspective | Key Questions |
|-----------|-------------|---------------|
| **Phase** | Business | Quarter goal achieved? ROI? Next quarter strategy? |
| **Goal** | Business | User value delivered? Epic prioritization appropriate? |
| **Epic** | AI behavior | What did AI do well? Poorly? Improvements? Instruction issues? |
| **Story** | AI behavior | What did AI do well? Poorly? Improvements? Instruction issues? |
| **Action Item** | AI behavior | What did AI do well? Poorly? Improvements? Instruction issues? |

## RETROSPECTIVE.md — AI Behavior Retrospective (Epic / Story / Action Item)

```markdown
# Retrospective: [Epic/Story/ACT name]

> Completed: [YYYY-MM-DD]

## Summary

| Item | Details |
|------|---------|
| **Objective** | [original objective] |
| **Result** | [actual result] |

## AI Did Well

- [Tasks/decisions AI performed effectively]

## AI Did Poorly

- [Areas where AI made mistakes/was inefficient/misjudged]

## AI Improvements

- [Specific behaviors AI should change in the next task]

## Instruction System Issues

- [Problems found in skills/rules/workflows]
- [Improvements to templates, procedures, output definitions]
```

## RETROSPECTIVE.md — Business Retrospective (Phase / Goal)

```markdown
# Retrospective: [Phase/Goal name]

> Completed: [YYYY-MM-DD]

## Summary

| Item | Details |
|------|---------|
| **Plan** | [original plan] |
| **Result** | [actual result] |
| **Effort** | [estimated vs actual] |

## Keep

- [What to maintain]

## Problem

- [Issues encountered]

## Try

- [What to try next time]

## Learned

- [Lessons learned]
```

## Retrospective Location

| Hierarchy | Location |
|-----------|----------|
| **Phase** | `workspace/phase/{phase_id}/RETROSPECTIVE.md` |
| **Goal** | `workspace/phase/{phase_id}/goals/{goal_id}/RETROSPECTIVE.md` |
| **Epic** | `workspace/phase/.../epics/{epic_name}/RETROSPECTIVE.md` |
| **Story** | `workspace/phase/.../epics/{epic_name}/{story_id}-{story_name}/RETROSPECTIVE.md` |

## Quality Criteria

- [ ] Is it written from the appropriate perspective (AI behavior vs. business)?
- [ ] Does each section contain at least one item?
- [ ] Are the improvements actionable for the next task?
