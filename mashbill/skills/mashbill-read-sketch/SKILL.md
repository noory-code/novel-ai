---
name: mashbill-read-sketch
user-invocable: true
description: Read the current Novel sketch and describe what is drawn — nodes, edges, and visible relationships.
metadata:
  version: "0.1.0"
  category: analysis
  type: unit
  style: analysis
  triggers: [plot read, read plot, describe plot, what is in my plot, summarise plot, summarize plot]
  uses: []
---

# /mashbill-read-sketch

Fetch the active Novel sketch and give the user a concise summary of what's drawn.

## When to run

The user wants an outside perspective on what they just drew — "what does this look like", "summarise", "does this hang together". Also useful at the start of a session to recall the state of a sketch you haven't seen in a while.

## Steps

1. Determine the project path from the user's message or the current working directory.
2. Call `list_sketches_tool(project_path)` to see what sketches exist.
3. Pick the sketch:
   - If the user named one, use it.
   - Otherwise use the most recently updated (the list is already sorted desc).
4. Call `get_sketch(project_path, sketch_id)` to get the full doc.
5. Report:
   - **Sketch name** and node / edge counts.
   - **Node clusters** — group nodes by colour or by connected-component and list their labels.
   - **Edge types** — group edges by label (or "unlabelled"). Flag orphan nodes (no incident edges).
   - **Gaps / questions** — name anything suspicious:
     - Orphans that probably shouldn't be isolated.
     - Edges without labels (ambiguous semantics).
     - Hubs (one node connected to >5 others).
     - Nodes with only `(untitled)` labels.
6. Do **not** rewrite the sketch in this skill — analysis only. If the user wants edits, hand off to `/mashbill-new-sketch` or direct MCP tool calls.

## Output shape

Keep it scannable:

```
📋 {name} — N nodes, M edges

Clusters:
- (colour / component) label1, label2, label3
- ...

Edge labels: "buys" × 2, "owns" × 1, (unlabelled) × 3

Flags:
- 2 orphans: X, Y
- Hub: Admin (7 edges)
- 1 untitled node
```

Then finish with a one-sentence read of the map.
