# Template: Status (Pending Approval)

Status document for work awaiting human approval.

## Location

```
{project_path}/workspace/pending/{task-name}/_status.md
```

> Rarely used. Prefer inline BLOCKING steps inside the relevant skill's Workflow. This template exists for ad-hoc human-approval gates outside the standard skill flow.

## Template

```markdown
# Pending Approval: [task name]

## Status
**Awaiting human approval**

## Prepared Work
- [x] Draft complete

## Items for Human Review
- [ ] Are the objectives appropriate?
- [ ] Is the decomposition appropriate?

## Next Steps After Approval
→ [next task]
```

## Quality Criteria

- [ ] Is the status clear?
- [ ] Are the items for human review organized as a checklist?
- [ ] Are the next steps after approval specified?
