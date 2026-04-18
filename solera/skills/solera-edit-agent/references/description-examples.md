# Description Field Examples for Agent Triggering

> The `description` field in an agent's frontmatter is **the primary mechanism by which Claude decides to invoke the agent**. A weak description means the agent never triggers when it should (or triggers when it shouldn't). This document catalogues good and bad patterns so agent authors can calibrate.

## Required shape

```yaml
description: Use this agent when {one-sentence triggering condition}. Examples:

<example>
Context: {short scene-setting — what is happening just before the user speaks}
user: "{exact or near-exact phrasing the user would use}"
assistant: "{what assistant says; must invoke this agent}"
<commentary>
{one-line rationale: why THIS agent and not another}
</commentary>
</example>

<example>
Context: {a DIFFERENT triggering context for the same agent}
user: "{different phrasing of the same intent}"
assistant: "..."
<commentary>
{rationale}
</commentary>
</example>
```

Two `<example>` blocks is the minimum. Four is the practical maximum. Each should trigger on a meaningfully different user phrasing or context.

## Good examples (copy freely)

### Analysis agent (`code-reviewer`)

```yaml
description: Use this agent when the user wants a pull request, diff, or staged changes reviewed for correctness, style, and security. Examples:

<example>
Context: Developer has just finished writing a feature and wants feedback.
user: "Review my changes before I open the PR"
assistant: "I'll use the code-reviewer agent to go through the diff and report findings."
<commentary>
Reactive review request — code-reviewer reads the diff and produces a prioritized findings list.
</commentary>
</example>

<example>
Context: Developer mentioned security concern mid-conversation.
user: "Can you check if the auth middleware change is safe?"
assistant: "I'll launch code-reviewer with a security focus on the auth middleware diff."
<commentary>
Scoped review — same agent, explicitly narrowed prompt.
</commentary>
</example>
```

### Generation agent (`test-generator`)

```yaml
description: Use this agent when the user asks to "write tests", "add unit tests", "cover this function with tests", or mentions missing test coverage on a specific file. Examples:

<example>
Context: Developer finished a pure function and wants coverage.
user: "Add tests for parseConfig in config.ts"
assistant: "I'll use the test-generator agent to produce unit tests for parseConfig."
<commentary>
Explicit generation request scoped to one function — test-generator reads the function and produces a matching test file.
</commentary>
</example>

<example>
Context: CI reported coverage dropped below threshold.
user: "Coverage fell below 80% on payment.ts, fix it"
assistant: "I'll launch test-generator on payment.ts with the uncovered lines as the target."
<commentary>
Coverage-driven invocation — same agent, different entry point (coverage report feeds the prompt).
</commentary>
</example>
```

### Team lead agent (`refactor-lead`)

```yaml
description: Use this agent when the user requests a multi-file refactor that needs coordinated changes across layers (e.g. rename a core API and propagate). The agent decomposes the work and dispatches to specialist agents (rename-agent, test-updater, import-fixer). Examples:

<example>
Context: Developer wants to rename a widely-used symbol.
user: "Rename calculateTax to computeTax everywhere"
assistant: "I'll use the refactor-lead agent to plan the rename and coordinate the specialists."
<commentary>
Multi-file rename — refactor-lead handles the planning + dispatch; individual specialists do the per-file edits.
</commentary>
</example>

<example>
Context: Developer wants a cross-layer change.
user: "Move the pricing logic from PricingService to a new PricingPolicy domain object"
assistant: "I'll bring in refactor-lead to plan the move and coordinate updates across the service, domain, and tests."
<commentary>
Architecture-level change spanning multiple layers — refactor-lead coordinates the layer-specific specialists.
</commentary>
</example>
```

## Bad examples (what goes wrong)

### Bad — generic one-liner

```yaml
description: Reviews code.
```

Why it fails: no triggering condition, no examples. Claude has no signal about when to invoke. Will trigger rarely or arbitrarily.

### Bad — examples without `<commentary>`

```yaml
description: Use this agent when the user wants code reviewed. Examples:

<example>
user: "review my PR"
assistant: "I'll review it."
</example>
```

Why it fails: no `Context` (so Claude can't tell if the scene matches the current conversation), no `<commentary>` (so Claude can't generalize to adjacent phrasings).

### Bad — examples that duplicate each other

```yaml
description: Use this agent to review code. Examples:

<example>
Context: User wants a review.
user: "review this"
assistant: "I'll review it."
<commentary>
Review requested.
</commentary>
</example>

<example>
Context: User wants a review again.
user: "please review"
assistant: "I'll review it."
<commentary>
Review requested.
</commentary>
</example>
```

Why it fails: two nearly-identical examples don't expand coverage. Spend the second example on a **different phrasing or context** — a proactive trigger, a scoped trigger, or an edge case.

### Bad — over-broad trigger

```yaml
description: Use this agent when the user asks about code, tests, documentation, or anything technical.
```

Why it fails: too broad. Every user turn is "about code" to some extent, so this agent will either always or never trigger. Be specific about the **decision point** — what has to be true before the agent is worth invoking rather than answering inline.

### Bad — banned phrases in the description itself

```yaml
description: Use this agent when code review is needed, depending on the situation.
```

Why it fails: "depending on the situation" is a Solera banned phrase and signals the author hasn't decided when to trigger. Replace with an explicit trigger: "Use this agent when the user requests a code review on a specific PR, diff, or staged changes."

## Calibration checklist

Before shipping an agent, verify the description:

- [ ] Opens with `"Use this agent when ..."`
- [ ] Has 2-4 `<example>` blocks
- [ ] Each example has `Context`, `user`, `assistant`, `<commentary>`
- [ ] Each example uses a **different** phrasing or context (no duplicates)
- [ ] At least one example shows a **proactive** trigger (the user didn't explicitly ask for the agent by name)
- [ ] Length between ~200 and ~1,000 characters
- [ ] No banned phrases (`as appropriate`, `if needed`, `depending on the situation`, `as you see fit`, `handle accordingly`)
- [ ] The triggering condition names a **decision point** — what must be true before invoking rather than answering inline
