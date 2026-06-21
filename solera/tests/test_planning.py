"""CORE-5 — planning: turn a goal into a Story and decompose it into Actions.

The decomposition judgement (where to split, what each gate should check) is the
agent's job, guided by the plan skill. But the *files* are created through
deterministic helpers so they always satisfy the CORE-1 conventions — the agent
never hand-writes frontmatter and cannot drift from the format.
"""

from pathlib import Path

from solera.planning import add_action, create_story, next_action_id, next_story_id
from solera.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / ".noory" / "solera")


def test_next_story_id_starts_at_001(tmp_path: Path) -> None:
    assert next_story_id(_ws(tmp_path)) == "STORY-001"


def test_next_story_id_increments_past_existing(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    create_story(ws, "first goal")
    create_story(ws, "second goal")
    assert next_story_id(ws) == "STORY-003"


def test_create_story_writes_compliant_file(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_story(ws, "Ship the thing.")
    assert story.id == "STORY-001"
    assert story.status == "todo"
    assert story.actions == []
    # 5c — it parses back through the guard unchanged.
    assert ws.load_story("STORY-001") == story


def test_next_action_id_increments_within_story(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_story(ws, "goal")
    assert next_action_id(story) == "ACT-001"
    add_action(ws, story.id, "do step one", gate="true")
    assert next_action_id(ws.load_story(story.id)) == "ACT-002"


def test_add_action_appends_and_writes_compliant_files(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_story(ws, "goal")
    action = add_action(ws, story.id, "Create out.txt", gate="test -f out.txt")
    assert action.id == "ACT-001"
    assert action.status == "todo"
    assert action.gate == "test -f out.txt"
    # Story now references the action, and both parse back through the guard.
    assert ws.load_story(story.id).actions == ["ACT-001"]
    assert ws.load_action(story.id, "ACT-001") == action


def test_decomposition_produces_runnable_plan(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_story(ws, "Build a two-step thing.")
    add_action(ws, story.id, "step one", gate="true")
    add_action(ws, story.id, "step two", gate="true")
    reread = ws.load_story(story.id)
    assert reread.actions == ["ACT-001", "ACT-002"]
    # Every referenced action has a parseable file — the plan is executable.
    for aid in reread.actions:
        assert ws.load_action(story.id, aid).status == "todo"
