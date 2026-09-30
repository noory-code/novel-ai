"""The command line over the WorkItem tree.

Skills tell the agent to run ``python -m solera <command>``. ``--root`` points at
the project directory; gates run there and ``.noory/solera/`` lives under it.
"""

import json
import shlex
import sys
from pathlib import Path

import pytest

from solera.cli import main
from solera.workspace import Workspace


def _file_gate(name: str) -> str:
    code = f"import os, sys; sys.exit(0 if os.path.exists({name!r}) else 1)"
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


def _run(root: Path, *args: str) -> int:
    return main(["--root", str(root), *args])


def _proposal_id(output: str) -> str:
    return next(
        line.removeprefix("proposal: ")
        for line in output.splitlines()
        if line.startswith("proposal: ")
    )


def test_plan_and_add_emit_ids(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    assert _run(tmp_path, "plan", "Build a thing.") == 0
    assert capsys.readouterr().out.strip() == "STORY-001"
    assert _run(tmp_path, "add", "STORY-001", "Step one", "--gate", "true") == 0
    assert capsys.readouterr().out.strip() == "ACT-001"


def test_plan_with_level(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    assert _run(tmp_path, "plan", "Stand up auth", "--level", "initiative") == 0
    assert capsys.readouterr().out.strip() == "INIT-001"


def test_plan_and_add_with_after(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    assert _run(tmp_path, "plan", "First", "--level", "initiative") == 0
    assert _run(tmp_path, "plan", "Story", "--after", "INIT-001") == 0
    assert (
        _run(
            tmp_path,
            "add",
            "STORY-001",
            "Step",
            "--gate",
            "true",
            "--after",
            "INIT-001",
        )
        == 0
    )
    capsys.readouterr()
    ws = Workspace(tmp_path / ".noory" / "solera")
    assert ws.load_item("STORY-001").after == ["INIT-001"]
    assert ws.load_item("ACT-001").after == ["INIT-001"]


def test_after_command_sets_and_clears_links(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Story")
    _run(tmp_path, "add", "STORY-001", "First", "--gate", "true")
    _run(tmp_path, "add", "STORY-001", "Second", "--gate", "true")
    capsys.readouterr()

    assert _run(tmp_path, "after", "ACT-002", "ACT-001") == 0
    assert capsys.readouterr().out.strip() == "ACT-002"
    ws = Workspace(tmp_path / ".noory" / "solera")
    assert ws.load_item("ACT-002").after == ["ACT-001"]

    assert _run(tmp_path, "after", "ACT-002") == 0
    assert capsys.readouterr().out.strip() == "ACT-002"
    assert ws.load_item("ACT-002").after == []
    assert "after:" not in ws.item_path("ACT-002").read_text()


def test_ready_prints_ready_and_blocked(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Not split", "--level", "initiative")
    _run(tmp_path, "plan", "Story")
    _run(
        tmp_path,
        "add",
        "STORY-001",
        "Blocked",
        "--gate",
        "true",
        "--after",
        "INIT-001",
    )
    _run(tmp_path, "add", "STORY-001", "Ready", "--gate", "true")
    capsys.readouterr()

    assert _run(tmp_path, "ready") == 0
    assert capsys.readouterr().out.splitlines() == [
        "ready: ACT-002",
        "blocked: ACT-001 waits for INIT-001",
    ]


def test_status_prints_progress_after_pointer(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Story")
    _run(tmp_path, "add", "STORY-001", "One", "--gate", "true")
    _run(tmp_path, "add", "STORY-001", "Two", "--gate", "true")
    ws = Workspace(tmp_path / ".noory" / "solera")
    ws.write_item(ws.load_item("ACT-001").model_copy(update={"status": "done"}))
    capsys.readouterr()

    assert _run(tmp_path, "status") == 0
    assert capsys.readouterr().out.splitlines() == [
        "pointer: (none)",
        "progress: STORY-001 1/2 50%",
    ]


def test_next_reports_when_no_leaf_can_start(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Not split", "--level", "initiative")
    _run(tmp_path, "plan", "Story")
    _run(
        tmp_path,
        "add",
        "STORY-001",
        "Blocked",
        "--gate",
        "true",
        "--after",
        "INIT-001",
    )
    capsys.readouterr()

    assert _run(tmp_path, "next") == 1
    output = capsys.readouterr().out
    assert output.startswith("error: no leaf can start")
    assert "INIT-001" in output


def test_next_prints_instruction(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Goal.")
    _run(tmp_path, "add", "STORY-001", "Make hello", "--gate", "true")
    capsys.readouterr()
    assert _run(tmp_path, "next") == 0
    out = capsys.readouterr().out
    assert "ACT-001" in out and "Make hello" in out


def test_full_loop_through_cli(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Produce a file.")
    _run(tmp_path, "add", "STORY-001", "Create out.txt", "--gate", _file_gate("out.txt"))
    _run(tmp_path, "next")
    capsys.readouterr()

    assert _run(tmp_path, "complete") == 1  # gate fails before the work
    capsys.readouterr()

    (tmp_path / "out.txt").write_text("done")
    assert _run(tmp_path, "complete") == 0
    assert "PASS" in capsys.readouterr().out

    assert _run(tmp_path, "next") == 0
    assert "nothing" in capsys.readouterr().out.lower()


def test_status_reports_audit_problems(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Goal.")
    _run(tmp_path, "add", "STORY-001", "Step", "--gate", "true")
    (tmp_path / ".noory" / "solera" / "items" / "ACT-001.md").unlink()  # break integrity
    capsys.readouterr()
    assert _run(tmp_path, "status") != 0
    assert "ACT-001" in capsys.readouterr().out


def _write_imported_release(root: Path, label: str, elements: list[dict[str, str]]) -> None:
    """Stand in for ``import_release`` with a validated vS + vP pair."""
    release_root = root / ".noory" / "solera" / "specs" / label
    service_dir = release_root / "service"
    project_dir = release_root / "project"
    service_dir.mkdir(parents=True, exist_ok=True)
    project_dir.mkdir(parents=True, exist_ok=True)
    release_number = int(label.removeprefix("v"))
    (service_dir / "manifest.json").write_text(
        json.dumps(
            {
                "format_f_version": 1,
                "scope": "service",
                "service": "service/auth",
                "release": f"vS{release_number}",
                "based_on": "vP1",
                "git_sha": "",
                "elements": [
                    {"id": "service/auth", "kind": "service", "hash": "c"},
                    *elements,
                ],
                "refs": {
                    "anchors": {"core_values": [], "identity": []},
                    "actors": [],
                    "entities": [],
                },
            }
        )
    )
    (project_dir / "manifest.json").write_text(
        json.dumps(
            {
                "format_f_version": 1,
                "scope": "project",
                "release": "vP1",
                "git_sha": "",
                "elements": [],
            }
        )
    )


def test_repin_proposes_without_mutating_by_default(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Goal.")
    _run(
        tmp_path, "add", "STORY-001", "Build login", "--gate", "true", "--realizes", "feature/login"
    )
    # mark it done so a reopen would be observable
    item_path = tmp_path / ".noory" / "solera" / "items" / "ACT-001.md"
    item_path.write_text(item_path.read_text().replace("status: todo", "status: done"))
    _write_imported_release(
        tmp_path, "v1", [{"id": "feature/login", "kind": "feature", "hash": "a"}]
    )
    _write_imported_release(
        tmp_path, "v2", [{"id": "feature/login", "kind": "feature", "hash": "b"}]
    )
    capsys.readouterr()

    assert _run(tmp_path, "repin", "v1", "v2") == 0
    out = capsys.readouterr().out
    assert "ACT-001" in out  # surfaced as a stale candidate
    assert "feature/login" in out  # the changed slug
    assert "shared changed:" in out
    assert "refs changed:" in out
    assert "proposal: " in out
    assert "ACT-001: realizes changed service element feature/login" in out
    # read-only: the item is still done (no --apply)
    assert "status: done" in item_path.read_text()


def test_repin_apply_reopens_stale_items(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Goal.")
    _run(
        tmp_path, "add", "STORY-001", "Build login", "--gate", "true", "--realizes", "feature/login"
    )
    item_path = tmp_path / ".noory" / "solera" / "items" / "ACT-001.md"
    item_path.write_text(item_path.read_text().replace("status: todo", "status: done"))
    _write_imported_release(
        tmp_path, "v1", [{"id": "feature/login", "kind": "feature", "hash": "a"}]
    )
    _write_imported_release(
        tmp_path, "v2", [{"id": "feature/login", "kind": "feature", "hash": "b"}]
    )
    capsys.readouterr()

    assert _run(tmp_path, "repin", "v1", "v2") == 0
    proposal_id = _proposal_id(capsys.readouterr().out)

    assert _run(tmp_path, "repin", "v1", "v2", "--apply", proposal_id) == 0
    assert "status: todo" in item_path.read_text()  # reopened


def test_repin_escalates_removed_but_never_reopens_it(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Goal.")
    _run(tmp_path, "add", "STORY-001", "Build old", "--gate", "true", "--realizes", "entity/old")
    item_path = tmp_path / ".noory" / "solera" / "items" / "ACT-001.md"
    item_path.write_text(item_path.read_text().replace("status: todo", "status: done"))
    _write_imported_release(tmp_path, "v1", [{"id": "entity/old", "kind": "entity", "hash": "a"}])
    _write_imported_release(tmp_path, "v2", [])  # removed
    capsys.readouterr()

    assert _run(tmp_path, "repin", "v1", "v2") == 0
    proposal_id = _proposal_id(capsys.readouterr().out)

    assert _run(tmp_path, "repin", "v1", "v2", "--apply", proposal_id) == 0
    out = capsys.readouterr().out
    assert "escalate" in out.lower() and "ACT-001" in out
    # removed → orphaned → a human decides; --apply must NOT reopen it
    assert "status: done" in item_path.read_text()


def test_repin_apply_requires_proposal_id(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(SystemExit) as exc_info:
        _run(tmp_path, "repin", "v1", "v2", "--apply")

    assert exc_info.value.code == 2
    assert "--apply" in capsys.readouterr().err


def test_repin_apply_rejects_wrong_proposal_id(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Goal.")
    _run(
        tmp_path, "add", "STORY-001", "Build login", "--gate", "true", "--realizes", "feature/login"
    )
    item_path = tmp_path / ".noory" / "solera" / "items" / "ACT-001.md"
    item_path.write_text(item_path.read_text().replace("status: todo", "status: done"))
    _write_imported_release(
        tmp_path, "v1", [{"id": "feature/login", "kind": "feature", "hash": "a"}]
    )
    _write_imported_release(
        tmp_path, "v2", [{"id": "feature/login", "kind": "feature", "hash": "b"}]
    )
    capsys.readouterr()

    assert _run(tmp_path, "repin", "v1", "v2", "--apply", "0" * 64) == 1
    assert "proposal changed" in capsys.readouterr().out
    assert "status: done" in item_path.read_text()


def test_repin_unknown_label_errors_cleanly(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "plan", "Goal.")
    capsys.readouterr()
    assert _run(tmp_path, "repin", "missing", "alsomissing") == 1
    assert "error:" in capsys.readouterr().out.lower()


def _write_published_bundle(pub: Path) -> Path:
    """Write a minimal format-F published bundle (a `vS` service release + the
    `vP` snapshot it is based on) and return the `vS` dir — the shape Novel's
    publish leaves on disk under `published/`."""
    vp = pub / "_project" / "vP1"
    (vp / "design").mkdir(parents=True)
    (vp / "manifest.json").write_text(
        json.dumps(
            {
                "format_f_version": 1,
                "scope": "project",
                "release": "vP1",
                "git_sha": "",
                "elements": [],
            }
        )
    )
    vs = pub / "service" / "vS1"
    (vs / "design").mkdir(parents=True)
    (vs / "manifest.json").write_text(
        json.dumps(
            {
                "format_f_version": 1,
                "scope": "service",
                "service": "service/auth",
                "release": "vS1",
                "based_on": "vP1",
                "git_sha": "",
                "elements": [
                    {"id": "service/auth", "kind": "service", "hash": "a"},
                ],
                "refs": {
                    "anchors": {"core_values": [], "identity": []},
                    "actors": [],
                    "entities": [],
                },
            }
        )
    )
    return vs


def test_import_copies_release_into_specs(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    vs = _write_published_bundle(tmp_path / "pub")
    capsys.readouterr()
    assert _run(tmp_path, "import", str(vs), "--label", "auth") == 0
    assert "auth" in capsys.readouterr().out
    specs = tmp_path / ".noory" / "solera" / "specs" / "auth"
    assert (specs / "service" / "manifest.json").exists()  # vS copied
    assert (specs / "project" / "manifest.json").exists()  # based_on vP copied


def test_import_duplicate_label_errors_cleanly(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    vs = _write_published_bundle(tmp_path / "pub")
    assert _run(tmp_path, "import", str(vs), "--label", "auth") == 0
    capsys.readouterr()
    assert _run(tmp_path, "import", str(vs), "--label", "auth") == 1  # re-import refused
    assert "error:" in capsys.readouterr().out.lower()


def test_retro_and_feedback_write_notes(tmp_path: Path) -> None:
    _run(tmp_path, "plan", "Goal.")
    assert _run(tmp_path, "retro", "STORY-001", "Learned a lot.") == 0
    assert (tmp_path / ".noory" / "solera" / "retros" / "STORY-001.md").exists()
    assert _run(tmp_path, "feedback", "FB-001", "Blocked here.") == 0
    assert (tmp_path / ".noory" / "solera" / "feedback" / "FB-001.md").exists()


@pytest.mark.parametrize(
    "arguments",
    [
        ("retro", "../outside", "body"),
        ("feedback", "../outside", "body"),
        ("add", "../outside", "goal"),
        ("plan", "goal", "--level", "../outside"),
        ("import", "missing", "--label", "../outside"),
        ("repin", "../outside", "new"),
    ],
)
def test_path_name_errors_are_reported_without_tracebacks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], arguments: tuple[str, ...]
) -> None:
    assert _run(tmp_path, *arguments) == 1
    output = capsys.readouterr()
    assert output.out.startswith("error: ")
    assert "Traceback" not in output.out
    assert output.err == ""
