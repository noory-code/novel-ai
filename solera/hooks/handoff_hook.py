#!/usr/bin/env python3
"""Solera hook handler for SessionEnd event.

Runs `claude -p` subprocess to automatically execute the handoff skill,
updating HANDOFF.md with current session context.

SessionEnd fires only when the actual user session ends, not when claude -p
subprocesses finish — preventing the recursive loop that Stop would cause.

Usage in hooks.json:
  "SessionEnd": [{
    "hooks": [{ "type": "command", "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/handoff_hook.py" }]
  }]
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


PROMPT = (
    "Run the handoff skill: "
    "1) Run git status --short, git log --oneline -5 to understand current session work. "
    "2) Read HANDOFF.md if it exists, or create it from scratch. "
    "3) Update these sections based on git output and todo list: "
    "current work, completed items, next steps, key decisions, reference files, caveats. "
    "4) Add a timestamp '> last updated: YYYY-MM-DD HH:MM' at the top. "
    "5) Save HANDOFF.md to the project root. "
    "Keep it concise — 2-3 lines per section maximum."
)


def main(stdin_data: str | None = None) -> tuple[str, str, int]:
    """Run the hook. Returns (stdout, stderr, exit_code)."""
    # Guard against recursive invocation: claude -p subprocesses also trigger
    # SessionEnd, which would re-enter this hook indefinitely.
    if os.environ.get("SOLERA_HANDOFF_RUNNING"):
        return "", "", 0

    stderr_parts: list[str] = []

    if stdin_data is None:
        try:
            stdin_data = sys.stdin.read().strip()
        except Exception:
            stdin_data = ""

    if not stdin_data:
        stderr_parts.append("solera-handoff-hook: no input received on stdin")
        return "", "\n".join(stderr_parts), 1

    try:
        hook_data = json.loads(stdin_data)
    except (json.JSONDecodeError, ValueError):
        stderr_parts.append("solera-handoff-hook: invalid JSON on stdin")
        return "", "\n".join(stderr_parts), 1

    cwd = hook_data.get("cwd")

    cmd = [
        "claude", "-p", PROMPT,
        "--model", "haiku",
        "--allowedTools", "Bash,Read,Write,Edit",
        "--output-format", "text",
    ]

    log_path = Path("/tmp/solera-handoff-hook.log")
    env = {**os.environ, "SOLERA_HANDOFF_RUNNING": "1"}
    try:
        with log_path.open("w", encoding="utf-8") as log_file:
            subprocess.run(
                cmd,
                stdout=log_file,
                stderr=log_file,
                env=env,
                cwd=cwd,
                shell=False,
                timeout=60,
                check=False,
            )
    except subprocess.TimeoutExpired:
        stderr_parts.append("solera-handoff-hook: timeout after 60s")
        return "", "\n".join(stderr_parts), 0
    except OSError as exc:
        stderr_parts.append(f"solera-handoff-hook: failed to launch claude -p: {exc}")
        return "", "\n".join(stderr_parts), 0

    stderr_parts.append("solera-handoff-hook: SessionEnd — HANDOFF.md updated")
    return "", "\n".join(stderr_parts), 0


if __name__ == "__main__":
    stdout, stderr, code = main()
    if stderr:
        print(stderr, file=sys.stderr)
    if stdout:
        sys.stdout.write(stdout)
    sys.exit(code)
