"""CORE-8 (capstone) — workspace audit: referential integrity across files.

Per-file parsing already fails fast (CORE-1). The audit is the cross-file guard:
every referenced Action has a file, no Action file is orphaned, and the pointer
points at things that exist. It reports problems rather than raising, so a tool
can show them all at once.
"""

from pathlib import Path

from solera.audit import audit_workspace
from solera.formats import Progress
from solera.planning import add_action, create_story
from solera.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / ".noory" / "solera")


def test_clean_workspace_has_no_problems(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_story(ws, "goal")
    add_action(ws, story.id, "step", gate="true")
    ws.write_progress(Progress(story=None, action=None))
    assert audit_workspace(ws) == []


def test_flags_referenced_action_with_no_file(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_story(ws, "goal")
    add_action(ws, story.id, "step", gate="true")
    ws.action_path(story.id, "ACT-001").unlink()  # delete the file, keep the reference
    problems = audit_workspace(ws)
    assert any("ACT-001" in p.detail and "missing" in p.detail.lower() for p in problems)


def test_flags_orphan_action_file(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_story(ws, "goal")  # no actions referenced
    ws.action_path(story.id, "ACT-999").write_text(
        "---\nstatus: todo\ngate: \"true\"\n---\nOrphan.\n"
    )
    problems = audit_workspace(ws)
    assert any("ACT-999" in p.detail and "orphan" in p.detail.lower() for p in problems)


def test_flags_pointer_to_missing_story(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    create_story(ws, "goal")
    ws.write_progress(Progress(story="STORY-404", action="ACT-001"))
    problems = audit_workspace(ws)
    assert any("STORY-404" in p.detail for p in problems)


def test_flags_malformed_story(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    ws.story_dir("STORY-001").mkdir(parents=True)
    ws.story_path("STORY-001").write_text("garbage, no frontmatter\n")
    problems = audit_workspace(ws)
    assert any("STORY-001" in p.detail for p in problems)
