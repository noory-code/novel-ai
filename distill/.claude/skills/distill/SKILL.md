---
name: distill
description: Extract and recall knowledge from Claude Code conversations
---

# /distill

When the user invokes `/distill <command>`, call the appropriate Distill MCP tool directly.

## Commands

### /distill init
→ Call `mcp__distill__init()`

### /distill ingest <path>
→ Call `mcp__distill__ingest(path="<path>")`
Requires `ANTHROPIC_API_KEY` (LLM extraction).

### /distill recall <query>
→ Call `mcp__distill__recall(query="<query>")`
No API key needed.

### /distill learn <transcript_path> <session_id>
→ Call `mcp__distill__learn(transcript_path="...", session_id="...")`
Requires `ANTHROPIC_API_KEY`.

### /distill crystallize
→ Call `mcp__distill__memory(action="crystallize")`
Requires `ANTHROPIC_API_KEY`.

### /distill profile
→ Call `mcp__distill__profile()`
No API key needed.

## Notes
- `recall`, `init`, `profile` work without any API key.
- `ingest`, `learn`, `crystallize` require `ANTHROPIC_API_KEY` (set in shell env).
- If Distill MCP server is not connected, tell the user to check their MCP config.
