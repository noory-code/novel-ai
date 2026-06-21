"""CORE-7 — artifact homes: staging + about/from tags + a misplacement guard.

Each kind of output has one home (see docs/ARTIFACT_HOMES.md). Process artifacts
— scratch output produced on the way — stage under stories/{id}/artifacts/ and
carry tags (about / from), not versions. The guard is light: it warns when
something landed in the wrong home, e.g. source code staged in artifacts (code
belongs in the repo).
"""

from pathlib import Path

import pytest

from solera.artifacts import (
    ArtifactRef,
    dump_manifest,
    find_misplaced_artifacts,
    parse_manifest,
)
from solera.errors import FormatError
from solera.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    ws = Workspace(tmp_path / ".noory" / "solera")
    ws.story_dir("STORY-001").mkdir(parents=True)
    return ws


# --- manifest (7b: tags, not versions) -------------------------------------


def test_parse_manifest_reads_about_and_from() -> None:
    text = (
        "---\n"
        "artifacts:\n"
        "  - file: erd.png\n"
        "    about: [feature/login]\n"
        "    from: dbml-export\n"
        "---\n"
    )
    manifest = parse_manifest(text)
    assert manifest == [ArtifactRef(file="erd.png", about=["feature/login"], from_="dbml-export")]


def test_manifest_round_trips() -> None:
    refs = [
        ArtifactRef(file="notes.md", about=[], from_=None),
        ArtifactRef(file="erd.png", about=["a", "b"], from_="tool"),
    ]
    assert parse_manifest(dump_manifest(refs)) == refs


@pytest.mark.parametrize(
    "text",
    [
        "no frontmatter\n",
        "---\nartifacts: notalist\n---\n",  # artifacts must be a list
        "---\nartifacts:\n  - about: [x]\n---\n",  # entry missing required file
        "---\nartifacts:\n  - file: x\n    version: 2\n---\n",  # versions are banned
    ],
)
def test_parse_manifest_rejects_malformed(text: str) -> None:
    with pytest.raises(FormatError):
        parse_manifest(text)


# --- misplacement guard (7c) -----------------------------------------------


def test_no_violation_for_clean_artifacts(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    adir = ws.artifacts_dir("STORY-001")
    adir.mkdir(parents=True)
    (adir / "notes.md").write_text("scratch notes")
    (adir / "diagram.png").write_text("binary-ish")
    assert find_misplaced_artifacts(ws) == []


def test_flags_source_code_staged_in_artifacts(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    adir = ws.artifacts_dir("STORY-001")
    adir.mkdir(parents=True)
    (adir / "module.py").write_text("print('belongs in the repo')")
    violations = find_misplaced_artifacts(ws)
    assert len(violations) == 1
    assert violations[0].path == adir / "module.py"
    assert "repo" in violations[0].reason


def test_guard_is_empty_when_no_artifacts_dir(tmp_path: Path) -> None:
    assert find_misplaced_artifacts(_ws(tmp_path)) == []
