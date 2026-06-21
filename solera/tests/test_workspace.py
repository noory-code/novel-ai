"""CORE-1a/1e — workspace layout + reading files off disk through the guard.

Layout::

    .noory/solera/
    ├── progress.md
    └── stories/
        └── <story-id>/
            ├── story.md
            └── <action-id>.md
"""

from pathlib import Path

import pytest

from solera.errors import FormatError
from solera.workspace import Workspace

PROGRESS = "---\nstory: STORY-001\naction: ACT-001\n---\n"
STORY = "---\nstatus: todo\nactions:\n  - ACT-001\n---\nBuild it.\n"
ACTION = "---\nstatus: todo\ngate: \"true\"\n---\nDo the thing.\n"


def _seed(root: Path) -> Workspace:
    ws = Workspace(root)
    ws.stories_dir.mkdir(parents=True)
    ws.progress_path.write_text(PROGRESS)
    (ws.story_dir("STORY-001")).mkdir()
    ws.story_path("STORY-001").write_text(STORY)
    ws.action_path("STORY-001", "ACT-001").write_text(ACTION)
    return ws


def test_paths_compose_from_root(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")
    assert ws.progress_path == ws.root / "progress.md"
    assert ws.stories_dir == ws.root / "stories"
    assert ws.story_dir("S1") == ws.root / "stories" / "S1"
    assert ws.story_path("S1") == ws.root / "stories" / "S1" / "story.md"
    assert ws.action_path("S1", "ACT-001") == ws.root / "stories" / "S1" / "ACT-001.md"


def test_load_round_trip(tmp_path: Path) -> None:
    ws = _seed(tmp_path)
    prog = ws.load_progress()
    assert prog.story == "STORY-001" and prog.action == "ACT-001"
    story = ws.load_story("STORY-001")
    assert story.id == "STORY-001" and story.actions == ["ACT-001"]
    action = ws.load_action("STORY-001", "ACT-001")
    assert action.id == "ACT-001" and action.gate == "true"


def test_list_stories_sorted(tmp_path: Path) -> None:
    ws = _seed(tmp_path)
    ws.story_dir("STORY-003").mkdir()
    ws.story_dir("STORY-002").mkdir()
    assert ws.list_stories() == ["STORY-001", "STORY-002", "STORY-003"]


def test_list_stories_empty_when_no_dir(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")
    assert ws.list_stories() == []


def test_load_missing_file_raises(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")
    with pytest.raises(FileNotFoundError):
        ws.load_progress()


def test_load_malformed_action_raises_format_error(tmp_path: Path) -> None:
    ws = _seed(tmp_path)
    ws.action_path("STORY-001", "ACT-001").write_text("garbage, no frontmatter\n")
    with pytest.raises(FormatError):
        ws.load_action("STORY-001", "ACT-001")
