# Lifecycle

All work items (Phase, Goal, Epic, Story, Action Item) have their concrete procedures defined in a `## Workflow` section.

## Core Principles

- **SSOT**: The `## Workflow` in each work item template is the single authoritative source of procedure
- **Workflow manager reads and executes**: does not define procedures directly

## Workflow Pattern

Work item Workflows are composed of Named Steps. Each Step has a clear role (Setup/Create/Execute/Wrap-up).

```markdown
## Workflow

### Step 0. Setup
- [ ] Check prerequisites → invoke parent skill if missing
- [ ] Create branch (if applicable)
- [ ] Status → 🔄

### Step 1. Create
- [ ] ... (handled by writing-* skills)

### Step 2. Execute
- [ ] ... concrete task steps ...

### Step 3. Wrap-up
- [ ] Confirm completion
- [ ] Status → ✅
- [ ] Determine next work item
```

## Workflow Location by Hierarchy

| Hierarchy | Template | Steps | Step Composition |
|-----------|----------|-------|-----------------|
| **Phase** | writing-phase/assets/phase-template.md | 4 | Setup → Create → Execute → Wrap-up |
| **Goal** | writing-goal/assets/goal-template.md | 4 | Setup → Create → Execute → Wrap-up |
| **Epic** | writing-epic/assets/epic-template.md | 4 | Setup → Create → Execute → Wrap-up |
| **Story** | writing-story/assets/story.md | 4 | Setup → Create → Execute → Wrap-up |
| **Action Item** | writing-action-item/assets/action-item.md | 3 | Setup → Execute → Wrap-up |

## Repeat Block Pattern

When iterating over child work items in the Execute Step, mark repeat blocks with HTML comments:

```markdown
### Step 2. Execute
<!-- Repeat the block below for each Story in the Stories table -->
#### Story: {US|TS}-NNN — {title}
- [ ] writing-story invoke
- [ ] Create Story branch
- [ ] Develop + complete
- [ ] Merge into Epic branch
<!-- /repeat -->
- [ ] Confirm all Stories complete
```

- **Template**: Define only 1 block between `<!-- repeat -->` and `<!-- /repeat -->`
- **Actual document**: writing-* skills expand the block to match the number of items in the table when creating work items
- **Progress tracking**: Individual checkboxes are created for each child work item, enabling progress tracking

## Workflow Manager Role

1. Read the `## Workflow` of the target work item
2. Execute each Step in order
3. Invoke writing-* skills when document creation is needed
4. Invoke frontend-*, dev-* skills when development work is needed
5. After completion, update progress.md + determine next work item
