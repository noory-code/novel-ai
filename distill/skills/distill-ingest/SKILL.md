---
name: distill-ingest
description: Extract knowledge from markdown/text files or directories.
metadata:
  version: "1.0.0"
  category: extraction
  type: unit
  style: tool
  triggers: [distill ingest, ingest docs, extract from files, distill import, ingest directory]
  uses: [mcp__distill__ingest]
---

# /distill-ingest

Extract knowledge from markdown, MDX, or text files into the knowledge store.

## Usage

```
/distill-ingest <path>
```

## MCP Tool

Call `mcp__distill__ingest` with:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | string | *required* | File or directory path to ingest |
| `scope` | string | None | Override scope: `global`, `workspace`, or `project` |

## Notes

- Recursively processes `.md`, `.mdx`, `.txt` files in directories
- Skips unchanged files automatically (mtime-based)
- Configure default ingest directories in `.distill/config.json` under `sources.dirs`
