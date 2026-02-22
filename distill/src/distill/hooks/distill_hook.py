#!/usr/bin/env python3
"""Distill hook handler for PreCompact and SessionEnd events.

Runs `claude -p` subprocess to extract knowledge from conversation transcripts
and store it via the distill MCP server.

Usage in hooks.json:
  "PreCompact": [{ "hooks": [{ "type": "command", "command": "python -m distill.hooks.distill_hook" }] }],
  "SessionEnd": [{ "hooks": [{ "type": "command", "command": "python -m distill.hooks.distill_hook" }] }]
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_claude_p(
    transcript_path: str,
    session_id: str,
    cwd: str | None,
    model: str = "haiku",
) -> str:
    """Extract knowledge via `claude -p` subprocess."""
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
        "--model", model,
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

    # Load config to get model name
    from distill.config import load_config
    config = load_config(cwd)

    try:
        result = _run_claude_p(transcript_path, session_id, cwd, model=config.extraction_model)
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
