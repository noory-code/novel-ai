"""The proof command line: record and query decisions."""

from pathlib import Path

from proof.cli import main


def _run(root: Path, *args: str) -> int:
    return main(["--root", str(root), *args])


def test_record_emits_id(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    assert _run(tmp_path, "record", "Use Postgres", "--body", "## Decision\nPostgres.") == 0
    assert capsys.readouterr().out.strip() == "PROOF-001"


def test_list_shows_decisions(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "record", "Use Postgres", "--body", "x")
    _run(tmp_path, "record", "Draft", "--status", "proposed", "--body", "y")
    capsys.readouterr()
    assert _run(tmp_path, "list") == 0
    out = capsys.readouterr().out
    assert "PROOF-001" in out and "[accepted]" in out
    assert "PROOF-002" in out and "[proposed]" in out


def test_in_force_drops_superseded(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "record", "Postgres", "--body", "x")
    _run(tmp_path, "record", "CockroachDB", "--supersedes", "PROOF-001", "--body", "y")
    capsys.readouterr()
    assert _run(tmp_path, "in-force") == 0
    out = capsys.readouterr().out
    assert "PROOF-002" in out and "PROOF-001" not in out


def test_show_prints_body(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "record", "Use Postgres", "--body", "## Decision\nPostgres it is.")
    capsys.readouterr()
    assert _run(tmp_path, "show", "PROOF-001") == 0
    out = capsys.readouterr().out
    assert "Use Postgres" in out and "Postgres it is." in out


def test_record_with_about_and_check(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    _run(tmp_path, "record", "Use Postgres", "--about", "ACT-005", "--body", "x")
    capsys.readouterr()
    # check is a gate: 0 when an in-force decision tags the id, 1 otherwise
    assert _run(tmp_path, "check", "--about", "ACT-005") == 0
    capsys.readouterr()
    assert _run(tmp_path, "check", "--about", "ACT-404") == 1
