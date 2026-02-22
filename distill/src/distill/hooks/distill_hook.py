#!/usr/bin/env python3
"""Distill hook handler for PreCompact and SessionEnd events.

Two-path auto-learn:
  1. If ANTHROPIC_API_KEY is set → extract knowledge directly via API + store in SQLite.
  2. Otherwise → run `claude -p` subprocess for immediate extraction (no API key needed).

Usage in .claude/settings.json:
  "hooks": {
    "PreCompact": [{ "command": "python -m distill.hooks.distill_hook" }],
    "SessionEnd": [{ "command": "python -m distill.hooks.distill_hook" }]
  }
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path


def _run_claude_p(
    transcript_path: str,
    session_id: str,
    cwd: str | None,
) -> str:
    """Extract knowledge via `claude -p` subprocess (no API key needed)."""
    distill_repo = str(Path(__file__).parent.parent.parent.parent)

    mcp_config = json.dumps({
        "mcpServers": {
            "distill": {
                "type": "stdio",
                "command": "uv",
                "args": ["--directory", distill_repo, "run", "python", "-m", "distill"],
            }
        }
    })

    prompt = (
        f'Read the transcript at "{transcript_path}". '
        "Extract reusable knowledge as JSON chunks "
        '[{"content":..., "type":..., "scope":..., "tags":..., "confidence":...}]. '
        f'Call mcp__distill__store(chunks=<array>, session_id="{session_id}").'
    )

    cmd = [
        "claude", "-p", prompt,
        "--allowedTools", "mcp__distill__store,Read",
        "--mcp-config", mcp_config,
        "--output-format", "text",
    ]

    result = subprocess.run(
        cmd,
        timeout=120,
        capture_output=True,
        text=True,
        cwd=cwd,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr[:300] or "claude -p exited non-zero")

    return result.stdout.strip() or "done"


async def _extract_and_store(
    transcript_path: str,
    session_id: str,
    cwd: str | None = None,
) -> str:
    """Extract knowledge via Anthropic API and store directly in SQLite."""
    from distill.extractor.extractor import extract_knowledge
    from distill.store.metadata import MetadataStore
    from distill.store.scope import detect_project_root, detect_workspace_root
    from distill.store.vector import VectorStore

    project_root = detect_project_root(cwd=cwd)
    workspace_root = detect_workspace_root(cwd=cwd)
    if workspace_root == project_root:
        workspace_root = None

    # ctx=None → skips MCP sampling, uses Anthropic API directly
    chunks = await extract_knowledge(
        ctx=None,
        transcript_path=transcript_path,
        session_id=session_id,
        trigger="session_end",
        project_name=Path(project_root).name if project_root else None,
        project_root=project_root,
    )

    if not chunks:
        return "No knowledge extracted."

    saved = 0
    for chunk in chunks:
        try:
            ws_root = workspace_root if chunk.scope == "workspace" else None
            with (
                MetadataStore(chunk.scope, project_root, ws_root) as meta,
                VectorStore(chunk.scope, project_root, ws_root) as vector,
            ):
                inserted = meta.insert(chunk)
                vector.index(inserted.id, inserted.content, inserted.tags)
                saved += 1
        except Exception:
            pass

    return f"Extracted {len(chunks)}, stored {saved}."


def main(stdin_data: str | None = None) -> tuple[str, str, int]:
    """Run the hook. Returns (stdout, stderr, exit_code).

    If stdin_data is None, reads from sys.stdin.
    """
    stderr_parts: list[str] = []

    # Read stdin
    if stdin_data is None:
        try:
            stdin_data = sys.stdin.read().strip()
        except Exception:
            stdin_data = ""

    if not stdin_data:
        stderr_parts.append("distill-hook: no input received on stdin")
        return "", "\n".join(stderr_parts), 1

    # Parse JSON
    try:
        hook_data = json.loads(stdin_data)
    except (json.JSONDecodeError, ValueError):
        stderr_parts.append("distill-hook: invalid JSON on stdin")
        return "", "\n".join(stderr_parts), 1

    session_id = hook_data.get("session_id")
    transcript_path = hook_data.get("transcript_path")

    if not session_id or not transcript_path:
        stderr_parts.append("distill-hook: missing session_id or transcript_path")
        return "", "\n".join(stderr_parts), 1

    event = hook_data.get("hook_event_name", "unknown")
    cwd = hook_data.get("cwd")
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if api_key:
        # Direct extraction via Anthropic API
        try:
            result = asyncio.run(_extract_and_store(transcript_path, session_id, cwd))
            stderr_parts.append(f"distill-hook: auto-learn complete — {result}")
        except Exception as err:
            stderr_parts.append(f"distill-hook: auto-learn failed: {err}")
            # Fallback: try claude -p
            try:
                result = _run_claude_p(transcript_path, session_id, cwd)
                stderr_parts.append(f"distill-hook: fallback claude -p complete — {result}")
            except Exception as fallback_err:
                stderr_parts.append(f"distill-hook: fallback claude -p failed: {fallback_err}")
    else:
        # No API key: use claude -p subprocess
        try:
            result = _run_claude_p(transcript_path, session_id, cwd)
            stderr_parts.append(f"distill-hook: {event} — auto-learn complete via claude -p")
        except Exception as err:
            stderr_parts.append(f"distill-hook: {event} — claude -p failed: {err}")

    return "", "\n".join(stderr_parts), 0


if __name__ == "__main__":
    stdout, stderr, code = main()
    if stderr:
        print(stderr, file=sys.stderr)
    if stdout:
        sys.stdout.write(stdout)
    sys.exit(code)
