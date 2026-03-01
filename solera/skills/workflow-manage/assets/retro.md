# Template: Retrospective

Write a RETRO.md when a hierarchy level is complete.

## Retrospective Types

| Hierarchy | Perspective | Key Questions |
|-----------|-------------|---------------|
| **Phase** | Business | Quarter goal achieved? ROI? Next quarter strategy? |
| **Goal** | Business | User value delivered? Epic prioritization appropriate? |
| **Epic** | AI behavior | What did AI do well? Poorly? Improvements? Instruction issues? |
| **Story** | AI behavior | What did AI do well? Poorly? Improvements? Instruction issues? |
| **Action Item** | AI behavior | What did AI do well? Poorly? Improvements? Instruction issues? |

## RETRO.md — AI Behavior Retrospective (Epic / Story / Action Item)

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

## RETRO.md — Business Retrospective (Phase / Goal)

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
| **Phase** | `workspace/phase/{phase_id}/RETRO.md` |
| **Goal** | `workspace/phase/{phase_id}/goals/{goal_id}/RETRO.md` |
| **Epic** | `workspace/phase/.../epics/{epic_name}/RETRO.md` |
| **Story** | `workspace/phase/.../stories/{story_id}/RETRO.md` |

## Quality Criteria

- [ ] Is it written from the appropriate perspective (AI behavior vs. business)?
- [ ] Does each section contain at least one item?
- [ ] Are the improvements actionable for the next task?
