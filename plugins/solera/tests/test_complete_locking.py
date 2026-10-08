"""Agent completion must release the workspace lock while a gate runs."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any

import pytest

from solera import cli, mcp_server
from solera.formats import Progress
from solera.planning import create_item
from solera.supervisor import cancel_item, complete, start_next
from solera.workspace import Workspace


def _slow_gate() -> str:
    import shlex
    import sys

    code = "from pathlib import Path; import time; Path('gate-started').touch(); time.sleep(1.0)"
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


def _running_completion(
    root: Path, surface: str
) -> tuple[Workspace, str, threading.Thread, dict[str, Any]]:
    ws = Workspace(root / ".noory" / "solera")
    leaf = create_item(ws, "action", "slow", gate=_slow_gate())
    assert start_next(ws) == leaf.id
    outcome: dict[str, Any] = {}

    def run() -> None:
        if surface == "core":
            outcome["result"] = complete(ws, leaf.id, cwd=root)
        elif surface == "mcp":
            outcome["result"] = mcp_server.complete_current(str(root))
        else:
            outcome["result"] = cli.main(["--root", str(root), "complete"])

    runner = threading.Thread(target=run)
    runner.start()
    deadline = time.monotonic() + 3.0
    while not (root / "gate-started").exists() and time.monotonic() < deadline:
        time.sleep(0.01)
    assert (root / "gate-started").exists()
    return ws, leaf.id, runner, outcome


@pytest.mark.parametrize("surface", ["core", "mcp", "cli"])
def test_agent_gate_does_not_hold_workspace_lock(tmp_path: Path, surface: str) -> None:
    ws, leaf_id, runner, outcome = _running_completion(tmp_path, surface)
    try:
        with ws.lock(timeout=0.2):
            pass
    finally:
        runner.join(timeout=3.0)

    assert not runner.is_alive()
    assert ws.load_item(leaf_id).status == "done"
    assert outcome["result"] is not None


@pytest.mark.parametrize("surface", ["core", "mcp"])
@pytest.mark.parametrize("change", ["gate", "cancel", "pointer", "accept"])
def test_changed_item_during_agent_gate_returns_conflict_without_writing(
    tmp_path: Path, change: str, surface: str
) -> None:
    ws, leaf_id, runner, outcome = _running_completion(tmp_path, surface)
    try:
        if change == "cancel":
            cancel_item(ws, leaf_id, "No longer needed")
        else:
            with ws.lock(timeout=0.2):
                if change == "pointer":
                    ws.write_progress(Progress(item=None))
                else:
                    value = "person" if change == "accept" else "true"
                    ws.write_item(ws.load_item(leaf_id).model_copy(update={change: value}))
    finally:
        runner.join(timeout=3.0)

    assert not runner.is_alive()
    result = outcome["result"]
    conflict = result.conflict if surface == "core" else result["conflict"]
    passed = result.passed if surface == "core" else result["passed"]
    stderr = result.stderr if surface == "core" else result["stderr"]
    assert conflict is True
    assert passed is False
    assert stderr == (
        f"{leaf_id} changed while its gate ran; nothing was written. Call next and continue."
    )
    assert ws.load_item(leaf_id).status == ("cancelled" if change == "cancel" else "doing")
    assert ws.load_item(leaf_id).gate_passed is False


def test_cli_reports_conflict_separately_from_gate_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ws, leaf_id, runner, outcome = _running_completion(tmp_path, "cli")
    try:
        with ws.lock(timeout=0.2):
            ws.write_progress(Progress(item=None))
    finally:
        runner.join(timeout=3.0)

    assert not runner.is_alive()
    assert outcome["result"] == 1
    output = capsys.readouterr().out
    assert f"CONFLICT {leaf_id}" in output
    assert f"FAIL {leaf_id}" not in output
    assert ws.load_item(leaf_id).status == "doing"
