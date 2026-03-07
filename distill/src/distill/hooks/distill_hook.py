#!/usr/bin/env python3
"""Distill hook handler for PreCompact and SessionEnd events.

Runs `claude -p` subprocess to extract knowledge from conversation transcripts
and store it via the distill MCP server.

Usage in hooks.json:
  "PreCompact": [{
    "hooks": [{ "type": "command", "command": "python -m distill.hooks.distill_hook" }]
  }],
  "SessionEnd": [{
    "hooks": [{ "type": "command", "command": "python -m distill.hooks.distill_hook" }]
  }]
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def _validate_inputs(
    transcript_path: str,
    session_id: str,
    cwd: str | None,
) -> tuple[Path, str, Path | None]:
    """Validate and normalize input values.

    Returns:
        (resolved_transcript_path, validated_session_id, resolved_cwd)

    Raises:
        ValueError: If any input is invalid
    """
    # Validate transcript_path
    try:
        resolved_transcript = Path(transcript_path).resolve()
    except (ValueError, OSError) as exc:
        raise ValueError(f"Invalid transcript_path: {exc}") from exc

    if not resolved_transcript.exists():
        raise ValueError(f"transcript_path does not exist: {resolved_transcript}")

    if not resolved_transcript.is_file():
        raise ValueError(f"transcript_path is not a file: {resolved_transcript}")

    # Validate session_id (only alphanumerics, hyphens, and underscores allowed)
    if not re.match(r'^[a-zA-Z0-9_-]+$', session_id):
        raise ValueError(
            f"Invalid session_id format: {session_id!r}. "
            "Only alphanumerics, hyphens, and underscores are allowed."
        )

    # Validate cwd
    resolved_cwd = None
    if cwd is not None:
        try:
            resolved_cwd = Path(cwd).resolve()
        except (ValueError, OSError) as exc:
            raise ValueError(f"Invalid cwd: {exc}") from exc

        if not resolved_cwd.is_dir():
            raise ValueError(f"cwd is not a directory: {resolved_cwd}")

    return resolved_transcript, session_id, resolved_cwd


def _run_claude_p(
    transcript_path: str,
    session_id: str,
    cwd: str | None,
    model: str = "haiku",
) -> str:
    """Extract knowledge via `claude -p` subprocess."""
    # Validate inputs
    resolved_transcript, validated_session_id, resolved_cwd = _validate_inputs(
        transcript_path, session_id, cwd
    )

    distill_repo = str(Path(__file__).parent.parent.parent.parent)

    venv_python = str(Path(distill_repo) / ".venv" / "bin" / "python")
    mcp_config = json.dumps({
        "mcpServers": {
            "distill": {
                "type": "stdio",
                "command": venv_python,
                "args": ["-m", "distill"],
            }
        }
    })

    prompt = (
        f'Read the transcript at "{resolved_transcript}". '
        "Extract reusable knowledge as JSON chunks "
        '[{"content":..., "type":..., "scope":..., "tags":..., "confidence":...}]. '
        f'Call mcp__distill__store(chunks=<array>, session_id="{validated_session_id}").'
    )

    cmd = [
        "claude", "-p", prompt,
        "--model", model,
        "--allowedTools", "mcp__distill__store,Read",
        "--mcp-config", mcp_config,
        "--output-format", "text",
    ]

    try:
        result = subprocess.run(
            cmd,
            timeout=120,
            capture_output=True,
            text=True,
            cwd=str(resolved_cwd) if resolved_cwd else None,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        # Terminate the process
        process = getattr(exc, "process", None)
        if process is not None:
            process.kill()
            process.wait()
        raise RuntimeError("Hook timed out after 120s — process forcefully terminated") from exc

    if result.returncode != 0:
        # Write full stderr to a temporary log file
        log_path = Path(f"/tmp/distill-hook-{validated_session_id}.log")
        try:
            log_path.write_text(result.stderr, encoding="utf-8")
            raise RuntimeError(
                f"claude -p failed (exit {result.returncode}). "
                f"Full log: {log_path}"
            )
        except OSError:
            # Fall back to inline message if log file write fails
            raise RuntimeError(
                f"claude -p failed (exit {result.returncode}): "
                f"{result.stderr or '(no stderr)'}"
            )

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
        _run_claude_p(transcript_path, session_id, cwd, model=config.extraction_model)
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
