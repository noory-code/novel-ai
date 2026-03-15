# Lifecycle

All work items (Phase, Goal, Epic, Story, Action Item) have their concrete procedures defined in a `## Workflow` section.

## Core Principles

- **SSOT**: The `## Workflow` in each work item template is the single authoritative source of procedure
- **Workflow manager reads and executes**: it does not define procedures directly

## Workflow Pattern

Work item workflows are composed of named steps. Each step has a clear role (Setup/Create/Execute/Wrap-up).

```markdown
## Workflow

### Step 0. Setup
- [ ] Check prerequisites → invoke parent skill if missing
- [ ] Create branch (if applicable)
- [ ] Status → 🔄

### Step 1. Create
- [ ] ... (handled by write-* skills)

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
| **Phase** | solera-write-phase/assets/phase-template.md | 4 | Setup → Create → Execute → Wrap-up |
| **Goal** | solera-write-goal/assets/goal-template.md | 4 | Setup → Create → Execute → Wrap-up |
| **Epic** | solera-write-epic/assets/epic-template.md | 4 | Setup → Create → Execute → Wrap-up |
| **Story** | solera-write-story/assets/story.md | 4 | Setup → Create → Execute → Wrap-up |
| **Action Item** | solera-execute-action-item/assets/action-item.md | 3 | Setup → Execute → Wrap-up |

## Repeat Block Pattern

When iterating over child work items in the Execute Step, mark repeat blocks with HTML comments:

```markdown
### Step 2. Execute
<!-- Repeat the block below for each Story in the Stories table -->
#### Story: {US|TS}-NNN — {title}
- [ ] solera-write-story invoke
- [ ] Create Story branch
- [ ] Develop + complete
- [ ] Merge into Epic branch
<!-- /repeat -->
- [ ] Confirm all Stories complete
```

- **Template**: Define only one block between `<!-- repeat -->` and `<!-- /repeat -->`
- **Actual document**: write-* skills expand the block to match the number of items in the table when creating work items
- **Progress tracking**: Individual checkboxes are created for each child work item, enabling progress tracking

## Workflow Manager Role

1. Read the `## Workflow` of the target work item
2. Execute each Step in order
3. Invoke write-* skills when document creation is needed
4. Invoke frontend-*, dev-* skills when development work is needed
5. After completion, update progress.md and determine the next work item
