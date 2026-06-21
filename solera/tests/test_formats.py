"""CORE-1 — file conventions: parse Action / Story / progress, reject malformed.

Invariant under test: the ``.noory/solera/`` workspace is plain files. Identity
lives in the path (filename / directory), never duplicated in frontmatter, so a
parser is handed the id explicitly and parses only status / gate / goal from text.
"""

import pytest
import yaml

from solera.errors import FormatError
from solera.formats import (
    Action,
    Progress,
    Story,
    dump_action,
    dump_progress,
    dump_story,
    parse_action,
    parse_progress,
    parse_story,
)

# --- Action ----------------------------------------------------------------

ACTION_OK = """\
---
status: todo
gate: "test -f output.txt"
---
Create output.txt with the build result.
"""


def test_parse_action_reads_status_gate_and_goal() -> None:
    act = parse_action(ACTION_OK, action_id="ACT-001")
    assert isinstance(act, Action)
    assert act.id == "ACT-001"
    assert act.status == "todo"
    assert act.gate == "test -f output.txt"
    assert act.goal == "Create output.txt with the build result."


def test_parse_action_allows_empty_gate() -> None:
    text = "---\nstatus: doing\ngate: \"\"\n---\nDo a thing.\n"
    act = parse_action(text, action_id="ACT-002")
    assert act.gate == ""
    assert act.status == "doing"


@pytest.mark.parametrize(
    "text",
    [
        "no frontmatter here\n",  # missing frontmatter fence
        "---\nstatus: todo\n---\nbody\n",  # missing required gate
        "---\ngate: \"x\"\n---\nbody\n",  # missing required status
        "---\nstatus: bogus\ngate: \"x\"\n---\nbody\n",  # invalid status enum
        "---\nstatus: todo\ngate: 5\n---\nbody\n",  # gate wrong type
        "---\nstatus: todo\ngate: \"x\"\nextra: nope\n---\nbody\n",  # unknown field
        "---\nstatus: todo\ngate: \"x\"\n---\n\n",  # empty goal body
    ],
)
def test_parse_action_rejects_malformed(text: str) -> None:
    with pytest.raises(FormatError):
        parse_action(text, action_id="ACT-XXX")


# --- Story -----------------------------------------------------------------

STORY_OK = """\
---
status: todo
actions:
  - ACT-001
  - ACT-002
---
Build the thing end to end.
"""


def test_parse_story_reads_status_actions_and_goal() -> None:
    story = parse_story(STORY_OK, story_id="STORY-001")
    assert isinstance(story, Story)
    assert story.id == "STORY-001"
    assert story.status == "todo"
    assert story.actions == ["ACT-001", "ACT-002"]
    assert story.goal == "Build the thing end to end."


def test_parse_story_allows_empty_action_list() -> None:
    text = "---\nstatus: todo\nactions: []\n---\nA goal with no actions yet.\n"
    story = parse_story(text, story_id="STORY-002")
    assert story.actions == []


@pytest.mark.parametrize(
    "text",
    [
        "plain text\n",  # missing frontmatter
        "---\nactions: []\n---\nbody\n",  # missing status
        "---\nstatus: todo\n---\nbody\n",  # missing actions
        "---\nstatus: nope\nactions: []\n---\nbody\n",  # invalid status
        "---\nstatus: todo\nactions: \"ACT-001\"\n---\nbody\n",  # actions not a list
        "---\nstatus: todo\nactions: [1, 2]\n---\nbody\n",  # action ids not strings
        "---\nstatus: todo\nactions: []\n---\n\n",  # empty goal
    ],
)
def test_parse_story_rejects_malformed(text: str) -> None:
    with pytest.raises(FormatError):
        parse_story(text, story_id="STORY-XXX")


# --- progress --------------------------------------------------------------


def test_parse_progress_reads_pointer() -> None:
    text = "---\nstory: STORY-001\naction: ACT-001\n---\n"
    prog = parse_progress(text)
    assert isinstance(prog, Progress)
    assert prog.story == "STORY-001"
    assert prog.action == "ACT-001"


def test_parse_progress_allows_null_pointer() -> None:
    text = "---\nstory: null\naction: null\n---\n"
    prog = parse_progress(text)
    assert prog.story is None
    assert prog.action is None


@pytest.mark.parametrize(
    "text",
    [
        "no frontmatter\n",
        "---\naction: ACT-001\n---\n",  # missing story key
        "---\nstory: STORY-001\n---\n",  # missing action key
        "---\nstory: 5\naction: ACT-001\n---\n",  # wrong type
        "---\nstory: S\naction: A\nextra: x\n---\n",  # unknown field
    ],
)
def test_parse_progress_rejects_malformed(text: str) -> None:
    with pytest.raises(FormatError):
        parse_progress(text)


# --- serialization round-trips (CORE-3 needs writers) ----------------------


def test_action_round_trips() -> None:
    act = parse_action(ACTION_OK, action_id="ACT-001")
    assert parse_action(dump_action(act), action_id="ACT-001") == act


def test_story_round_trips() -> None:
    story = parse_story(STORY_OK, story_id="STORY-001")
    assert parse_story(dump_story(story), story_id="STORY-001") == story


def test_progress_round_trips() -> None:
    text = "---\nstory: STORY-001\naction: ACT-001\n---\n"
    prog = parse_progress(text)
    assert parse_progress(dump_progress(prog)) == prog


def test_progress_null_round_trips() -> None:
    prog = parse_progress("---\nstory: null\naction: null\n---\n")
    rt = parse_progress(dump_progress(prog))
    assert rt.story is None and rt.action is None


def test_dump_action_preserves_gate_with_special_chars() -> None:
    gate = "python -c \"import os; print('hi: there')\""
    # build via parse from a YAML-safe dump instead of hand-quoting
    src = "---\n" + yaml.safe_dump({"status": "todo", "gate": gate}).strip() + "\n---\nGoal.\n"
    act = parse_action(src, action_id="ACT-009")
    assert act.gate == gate
    assert parse_action(dump_action(act), action_id="ACT-009").gate == gate
