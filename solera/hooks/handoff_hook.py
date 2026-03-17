#!/usr/bin/env python3
"""Solera hook handler for PreCompact event.

Runs `claude -p` subprocess to automatically update HANDOFF.md
before context compaction, preserving session state.

Usage in hooks.json:
  "PreCompact": [{
    "hooks": [{ "type": "command", "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/handoff_hook.py" }]
  }]
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path


PROMPT = (
    "Run the solera-handoff skill: "
    "1) Run git status --short, git log --oneline -5 to understand current session work. "
    "2) Read HANDOFF.md if it exists, or create it from scratch. "
    "3) Update these sections based on git output and todo list: "
    "current work, completed items, next steps, key decisions, reference files, caveats. "
    "4) Add a timestamp '> last updated: YYYY-MM-DD HH:MM' at the top. "
    "5) Save HANDOFF.md to the project root. "
    "Keep it concise — 2-3 lines per section maximum."
)

_LOCK_FILE = Path(tempfile.gettempdir()) / "solera-handoff-hook.lock"
_LOCK_TTL_SECONDS = 120


def _is_locked() -> bool:
    """Check if another handoff hook is running or ran recently."""
    if not _LOCK_FILE.exists():
        return False
    try:
        age = time.time() - _LOCK_FILE.stat().st_mtime
        return age < _LOCK_TTL_SECONDS
    except OSError:
        return False


def main(stdin_data: str | None = None) -> tuple[str, str, int]:
    """Run the hook. Returns (stdout, stderr, exit_code)."""
    # Guard against concurrent invocation.
    # Lockfile with TTL — NOT deleted after run, expires after 120s.
    if _is_locked():
        return "", "", 0
    _LOCK_FILE.write_text(str(time.time()), encoding="utf-8")

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

    # Only run in the plugin's home project — skip other projects that
    # happen to have solera enabled (e.g. flutter-material-kit).
    plugin_project_root = Path(__file__).resolve().parent.parent.parent
    if cwd and not Path(cwd).resolve().is_relative_to(plugin_project_root):
        return "", "", 0

    cmd = [
        "claude", "-p", PROMPT,
        "--model", "haiku",
        "--allowedTools", "Bash,Read,Write,Edit",
        "--output-format", "text",
    ]

    log_path = Path(tempfile.gettempdir()) / "solera-handoff-hook.log"
    try:
        with log_path.open("w", encoding="utf-8") as log_file:
            subprocess.run(
                cmd,
                stdout=log_file,
                stderr=log_file,
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

    stderr_parts.append("solera-handoff-hook: PreCompact — HANDOFF.md updated")
    return "", "\n".join(stderr_parts), 0


if __name__ == "__main__":
    stdout, stderr, code = main()
    if stderr:
        print(stderr, file=sys.stderr)
    if stdout:
        sys.stdout.write(stdout)
    sys.exit(code)
