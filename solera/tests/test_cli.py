"""The command line — the surface an external agent uses to drive Solera.

Skills tell the agent to run ``python -m solera <command>``; these are the
deterministic scripts behind the file+skill+script model. The CLI never builds
anything — it plans, hands out the next instruction, runs gates, and records
notes. ``--root`` points at the project directory (gates run there;
``.noory/solera/`` lives under it).
"""

import shlex
import sys
from pathlib import Path

from solera.cli import main


def _file_gate(name: str) -> str:
    code = f"import os, sys; sys.exit(0 if os.path.exists({name!r}) else 1)"
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


def _run(root: Path, *args: str) -> int:
    return main(["--root", str(root), *args])


def test_plan_and_add_emit_ids(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    assert _run(tmp_path, "plan", "Build a thing.") == 0
    assert capsys.readouterr().out.strip() == "STORY-001"
    assert _run(tmp_path, "add", "STORY-001", "Step one", "--gate", "true") == 0
    assert capsys.readouterr().out.strip() == "ACT-001"


def test_next_prints_instruction(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Goal.")
    _run(tmp_path, "add", "STORY-001", "Make hello.txt", "--gate", "true")
    capsys.readouterr()
    assert _run(tmp_path, "next") == 0
    out = capsys.readouterr().out
    assert "ACT-001" in out and "Make hello.txt" in out


def test_full_loop_through_cli(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Produce a file.")
    _run(tmp_path, "add", "STORY-001", "Create out.txt", "--gate", _file_gate("out.txt"))
    _run(tmp_path, "next")
    capsys.readouterr()

    # gate fails before the agent does the work
    assert _run(tmp_path, "complete") == 1
    capsys.readouterr()

    # agent does the work, gate passes
    (tmp_path / "out.txt").write_text("done")
    assert _run(tmp_path, "complete") == 0
    assert "PASS" in capsys.readouterr().out

    # nothing left open
    assert _run(tmp_path, "next") == 0
    assert "nothing" in capsys.readouterr().out.lower()


def test_status_reports_audit_problems(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Goal.")
    _run(tmp_path, "add", "STORY-001", "Step", "--gate", "true")
    # break referential integrity
    (tmp_path / ".noory" / "solera" / "stories" / "STORY-001" / "ACT-001.md").unlink()
    capsys.readouterr()
    assert _run(tmp_path, "status") != 0
    assert "ACT-001" in capsys.readouterr().out


def test_retro_and_feedback_write_notes(tmp_path: Path) -> None:
    _run(tmp_path, "plan", "Goal.")
    assert _run(tmp_path, "retro", "STORY-001", "Learned a lot.") == 0
    assert (tmp_path / ".noory" / "solera" / "stories" / "STORY-001" / "RETROSPECTIVE.md").exists()
    assert _run(tmp_path, "feedback", "FB-001", "Blocked here.") == 0
    assert (tmp_path / ".noory" / "solera" / "feedback" / "FB-001.md").exists()
