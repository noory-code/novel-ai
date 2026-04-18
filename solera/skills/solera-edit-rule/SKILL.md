---
name: solera-edit-rule
user-invocable: true
description: Use this skill when the user asks to "create a rule", "add a coding rule", "write a project convention as a rule", "turn this constraint into a rule file", or "audit a rule for clarity". Produces a structured .claude/rules/{name}.md with YAML frontmatter (name, description, version, applies_to), Scope, verifiable Checklist, and concrete Good/Bad examples — line count capped at 200.
metadata:
  version: "2.1.0"
  category: meta
  type: unit
  style: procedural
  triggers: [create a rule, edit a rule, improve a rule, review a rule, add a coding rule]
  uses: []
---

# Edit Rule

## Input

| Parameter | Required | Description | Example |
|---|---|---|---|
| action | Y | create \| review \| improve | create |
| rule_name | N | Name for the new rule (required when action=create) | commit-format |
| rule_path | N | Path to existing rule file (required when action=review or improve) | .claude/rules/commit-format.md |

## Output

| Step | Output | Path |
|---|---|---|
| Create | Rule definition file | `.claude/rules/{rule_name}.md` |

---

## Procedure

### CREATE

**Step 1: Gather requirements**

- [ ] Clarify scope: when does this rule apply?
- [ ] Define checklist items (must be verifiable, not subjective)
- [ ] Prepare Good/Bad examples

**Step 2: Write rule file** — ref: [assets/rule-template.md](assets/rule-template.md)

- [ ] Frontmatter filled (`name`, `description`, `version`, `applies_to`). `description` names 2-3 concrete triggers. `applies_to` is a bounded glob/area, not "everywhere".
- [ ] Keep under 200 lines
- [ ] Scope statement present
- [ ] Checklist included
- [ ] Good/Bad examples included

**Step 3: Validate**

- [ ] Frontmatter present and complete
- [ ] Scope is explicit (not "when appropriate")
- [ ] Each checklist item is independently verifiable
- [ ] Good/Bad examples are concrete, not generic

---

### REVIEW

**Step 4: Analyze existing rule**

- [ ] Frontmatter present with `name`, `description`, `version`, `applies_to`
- [ ] Line count ≤ 200
- [ ] Scope statement is clear
- [ ] Checklist items are verifiable
- [ ] Good/Bad examples are specific

**Step 5: Generate review report**

- Summarize findings and recommendations

---

### IMPROVE

**Step 6: Run review (invoke steps 4-5)**

- Obtain review report

**Step 7: Apply improvements**

- [ ] Apply review findings
- [ ] Re-validate all criteria

---

## Completion Checklist

- [ ] `.claude/rules/{rule_name}.md` created
- [ ] Frontmatter present (`name`, `description`, `version`, `applies_to`)
- [ ] Line count ≤ 200
- [ ] Scope statement present
- [ ] Checklist included
- [ ] Good/Bad examples included
