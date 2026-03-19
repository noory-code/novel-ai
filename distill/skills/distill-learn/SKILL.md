---
name: distill-learn
user-invocable: true
description: Extract knowledge from a conversation transcript.
metadata:
  version: "1.0.0"
  category: extraction
  type: unit
  style: tool
  triggers: [distill learn, extract knowledge, learn from transcript, distill extract]
  uses: [mcp__distill__learn]
---

# /distill-learn

Extract knowledge from a conversation transcript file (.jsonl).

## Usage

```
/distill-learn <transcript_path> <session_id>
```

## MCP Tool

Call `mcp__distill__learn` with:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `transcript_path` | string | *required* | Path to .jsonl transcript file |
| `session_id` | string | *required* | Session identifier |
| `scope` | string | None | Override scope: `global`, `workspace`, or `project` |

## Notes

- Uses MCP Sampling (no API key needed) — routes through your Claude subscription
- Hooks call this automatically at session end; manual use is for re-processing
- Auto-triggers crystallization if threshold is met (configurable in `.distill/config.json`)
