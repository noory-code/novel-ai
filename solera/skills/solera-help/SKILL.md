---
name: solera-help
user-invocable: true
description: Explain what Solera is and how its plan / run / retro / feedback skills fit together.
metadata:
  version: "6.0.0"
  category: meta
  type: unit
  style: guide
  triggers: [what is solera, solera help, solera get started, how to use solera]
  uses: [solera-plan, solera-run, solera-retro, solera-feedback]
---

# Solera

Solera is a slim **harness**. It does not build anything itself — you (the agent)
do the building. Solera plans the work into a tree, hands you one leaf at a time,
and runs a deterministic **gate** to verify each leaf before moving on.

It works standalone, with or without Plot, over plain files under
`.noory/solera/` in the project directory.

## The tree

Work is one tree of **WorkItems** at any altitude — `initiative` / `epic` /
`story` / `action` (`level` is just a label). A **leaf** has a gate and no
children (the chunk you actually build, finishable in one context). A
**container** has children and no gate (it only rolls up their status). Size is
an altitude: the leaf stays one-context + one-gate, everything above is grouping.

## The loop

```mermaid
flowchart LR
  Plan[plan + add: build the tree] --> Next[next: take the next leaf]
  Next --> Work[you build it]
  Work --> Gate[complete: run the gate]
  Gate -->|pass| Next
  Gate -->|fail| Stop[stop, escalate to a human]
```

## Commands

Run the CLI from the project directory (gates run there):

```bash
uv run --directory "${CLAUDE_PLUGIN_ROOT}" solera --root "$PWD" <command>
```

| Command | What it does |
|---|---|
| `plan "<goal>" [--level L]` | Create a root WorkItem; prints its id. See **solera-plan**. |
| `add <parent> "<goal>" [--level L] [--gate "<cmd>"]` | Add a child under a parent (a leaf if you pass `--gate`). |
| `next` | Mark the next open leaf `doing` and print its instruction. See **solera-run**. |
| `complete` | Run the active leaf's gate; pass -> `done` + rollup, fail -> stop. |
| `status` | Show the pointer and any tree-integrity problems. |
| `retro <item> "<text>"` | Record what the design lacked. See **solera-retro**. |
| `feedback <id> "<text>"` | Record a blocker for a human. See **solera-feedback**. |

## Rules

- One leaf = one chunk you can finish in a single context, with a gate that
  proves it is done. Bigger work is a container of smaller items.
- Never edit files under `.noory/solera/` by hand — use the commands, which keep
  the format valid.
- A gate that fails leaves the leaf stuck on purpose. Fix the work and re-run
  `complete`, or write `feedback` and stop for a human.
