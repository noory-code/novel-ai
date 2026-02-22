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

### /distill recall <query>
→ Call `mcp__distill__recall(query="<query>")`

### /distill learn <transcript_path> <session_id>
→ Call `mcp__distill__learn(transcript_path="...", session_id="...")`

### /distill crystallize
→ Call `mcp__distill__memory(action="crystallize")`

### /distill profile
→ Call `mcp__distill__profile()`

## Notes
- All tools use MCP Sampling for LLM calls (no API key needed).
- Hooks use `claude -p` subprocess for automatic extraction at session end.
- If Distill MCP server is not connected, tell the user to check their MCP config.
