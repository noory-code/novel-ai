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
from solera.gate import GateResult, run_gate, run_item_gate, run_proof_gate


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


def test_proof_gate_reads_plain_file_contract(tmp_path: Path) -> None:
    proof_root = tmp_path / ".noory" / "proof"
    proof_root.mkdir(parents=True)
    (proof_root / "PROOF-001.md").write_text(
        "---\ntitle: Use Postgres\nstatus: accepted\nsupersedes: null\n"
        "about: [auth-stack]\n---\nBecause.\n",
        encoding="utf-8",
    )
    assert run_proof_gate("auth-stack", cwd=tmp_path).passed is True
    assert run_proof_gate("other", cwd=tmp_path).passed is False


def test_proof_gate_ignores_superseded_decision(tmp_path: Path) -> None:
    proof_root = tmp_path / ".noory" / "proof"
    proof_root.mkdir(parents=True)
    (proof_root / "PROOF-001.md").write_text(
        "---\ntitle: Old\nstatus: accepted\nsupersedes: null\nabout: [auth-stack]\n---\nOld.\n",
        encoding="utf-8",
    )
    (proof_root / "PROOF-002.md").write_text(
        "---\ntitle: New\nstatus: accepted\nsupersedes: PROOF-001\n"
        "about: [replacement]\n---\nNew.\n",
        encoding="utf-8",
    )
    assert run_proof_gate("auth-stack", cwd=tmp_path).passed is False


def test_proof_gate_fails_closed_on_malformed_log(tmp_path: Path) -> None:
    proof_root = tmp_path / ".noory" / "proof"
    proof_root.mkdir(parents=True)
    (proof_root / "PROOF-001.md").write_text("not frontmatter\n", encoding="utf-8")
    result = run_proof_gate("auth-stack", cwd=tmp_path)
    assert result.passed is False
    assert "could not read Proof log" in result.stderr
