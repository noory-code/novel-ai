"""CORE-2 — gate-runner: deterministic subprocess, exit-code verdict, edges.

The gate is the V (verification) of the harness. It must be deterministic and
shell-independent: the command string is tokenised and run with ``shell=False``
so the verdict never depends on a shell being present. exit 0 == pass, anything
else == fail, with stdout/stderr captured as evidence.
"""

import shlex
import sys
from pathlib import Path

import pytest

from solera.errors import GateError
from solera.formats import WorkItem
from solera.gate import GateResult, run_gate, run_item_gate


def _py(code: str) -> str:
    """A shell-independent command that runs Python with the given source."""
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


def test_exit_zero_passes() -> None:
    res = run_gate(_py("import sys; sys.exit(0)"), cwd=Path.cwd())
    assert isinstance(res, GateResult)
    assert res.passed is True
    assert res.exit_code == 0
    assert res.timed_out is False


def test_nonzero_exit_fails() -> None:
    res = run_gate(_py("import sys; sys.exit(3)"), cwd=Path.cwd())
    assert res.passed is False
    assert res.exit_code == 3


def test_captures_stdout_and_stderr() -> None:
    code = "import sys; print('OUT'); print('ERR', file=sys.stderr); sys.exit(1)"
    res = run_gate(_py(code), cwd=Path.cwd())
    assert "OUT" in res.stdout
    assert "ERR" in res.stderr
    assert res.passed is False


def test_timeout_fails_and_flags() -> None:
    res = run_gate(_py("import time; time.sleep(5)"), cwd=Path.cwd(), timeout=0.5)
    assert res.passed is False
    assert res.timed_out is True
    assert res.exit_code is None


def test_command_not_found_fails_without_raising() -> None:
    res = run_gate("definitely-not-a-real-command-xyz --flag", cwd=Path.cwd())
    assert res.passed is False
    assert res.timed_out is False
    assert res.exit_code is None
    assert res.stderr


@pytest.mark.parametrize("command", ["", "   ", "\n"])
def test_empty_command_raises(command: str) -> None:
    with pytest.raises(GateError):
        run_gate(command, cwd=Path.cwd())


def test_runs_in_given_cwd(tmp_path: Path) -> None:
    (tmp_path / "marker.txt").write_text("hi")
    code = "import os, sys; sys.exit(0 if os.path.exists('marker.txt') else 1)"
    assert run_gate(_py(code), cwd=tmp_path).passed is True
    assert run_gate(_py(code), cwd=Path.cwd()).passed is False


# --- leaf-item wrapper -----------------------------------------------------


def test_run_item_gate_reads_gate_from_leaf(tmp_path: Path) -> None:
    (tmp_path / "out.txt").write_text("done")
    gate = _py("import os, sys; sys.exit(0 if os.path.exists('out.txt') else 1)")
    item = WorkItem(id="ACT-001", level="action", status="doing", gate=gate, goal="make out.txt")
    assert run_item_gate(item, cwd=tmp_path).passed is True


def test_run_item_gate_without_gate_raises(tmp_path: Path) -> None:
    item = WorkItem(id="ACT-002", level="action", status="doing", goal="no gate")
    with pytest.raises(GateError):
        run_item_gate(item, cwd=tmp_path)
