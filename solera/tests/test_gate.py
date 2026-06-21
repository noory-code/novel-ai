"""CORE-2 — gate-runner: deterministic subprocess, exit-code verdict, edges.

The gate is the V (verification) of the harness. It must be deterministic and
shell-independent: the command string is tokenised and run with ``shell=False``
so the verdict never depends on a shell being present or on shell expansion.
exit 0 == pass, anything else == fail, with stdout/stderr captured as evidence.
"""

import shlex
import sys
from pathlib import Path

import pytest
import yaml

from solera.errors import GateError
from solera.formats import parse_action
from solera.gate import GateResult, run_action_gate, run_gate


def _py(code: str) -> str:
    """A shell-independent command that runs Python with the given source."""
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


def _action_text(gate: str, *, status: str = "doing", goal: str = "Do it.") -> str:
    """Build an Action file with YAML-safe frontmatter around an arbitrary gate."""
    fm = yaml.safe_dump({"status": status, "gate": gate}, default_flow_style=False).strip()
    return f"---\n{fm}\n---\n{goal}\n"


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
    assert res.stderr  # carries the reason


@pytest.mark.parametrize("command", ["", "   ", "\n"])
def test_empty_command_raises(command: str) -> None:
    with pytest.raises(GateError):
        run_gate(command, cwd=Path.cwd())


def test_runs_in_given_cwd(tmp_path: Path) -> None:
    (tmp_path / "marker.txt").write_text("hi")
    code = "import os, sys; sys.exit(0 if os.path.exists('marker.txt') else 1)"
    assert run_gate(_py(code), cwd=tmp_path).passed is True
    assert run_gate(_py(code), cwd=Path.cwd()).passed is False


# --- Action wrapper (2d) ---------------------------------------------------


def test_run_action_gate_reads_gate_from_action(tmp_path: Path) -> None:
    (tmp_path / "out.txt").write_text("done")
    gate = _py("import os, sys; sys.exit(0 if os.path.exists('out.txt') else 1)")
    action = parse_action(_action_text(gate), action_id="ACT-001")
    res = run_action_gate(action, cwd=tmp_path)
    assert res.passed is True


def test_run_action_gate_without_gate_raises(tmp_path: Path) -> None:
    text = "---\nstatus: doing\ngate: \"\"\n---\nNo gate here.\n"
    action = parse_action(text, action_id="ACT-002")
    with pytest.raises(GateError):
        run_action_gate(action, cwd=tmp_path)
