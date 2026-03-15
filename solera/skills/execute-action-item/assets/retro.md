# Action Item Retrospective Rules

> Follow these rules when writing RETRO.md in the Wrap-up Step.
> Template: [manage-workflow/assets/retro.md](../../manage-workflow/assets/retro.md) — use "AI Behavior Retrospective".

## Perspective: AI Behavior

Action Item retrospectives focus on **AI behavior** (not a business retrospective).

## Required Sections

| Section | Writing Guide |
|---------|---------------|
| **AI Did Well** | Coding quality, TDD execution, skill selection, commit accuracy |
| **AI Did Poorly** | Build/test failures, incorrect skill invocation, unnecessary repetition |
| **AI Improvements** | Specific behaviors AI should change in the next Action Item |
| **Instruction System Issues** | Omissions, ambiguities, or errors in skill/rule/workflow definitions |

## Action Item-Specific Review Questions

- Was the commit scope appropriate — neither too large nor too small?
- Was the development skill selection appropriate?
- Was the TDD procedure (Red → Green) followed correctly?
- Were there unexpected issues during build or testing?
- Was there unnecessary repetition (retrying the same approach that already failed)?
- Could a more efficient approach have been taken?

## Location

Write the retrospective as a `## Retrospective` section **inside the Action Item file itself** (`action-items/ACT-NNN-{name}.md`), not as a separate file.

> The next Action Item's Setup step reads previous ACT files to pick up "Improvements" before starting.
