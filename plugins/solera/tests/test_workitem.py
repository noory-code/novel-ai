"""D2-2 — the recursive WorkItem: one node type for the whole altitude ladder.

A WorkItem is any rung — initiative, epic, story, or action. ``level`` is a free
label (the conventional ladder is initiative/epic/story/action). The invariant
that keeps the tree executable: a leaf carries a ``gate`` and no children; a
container carries children and no gate. An item may have neither yet (a
container awaiting decomposition), but never both — it cannot be leaf and
container at once.
"""

import pytest
from pydantic import ValidationError

from solera.errors import FormatError
from solera.formats import WorkItem, dump_workitem, parse_workitem


def test_legacy_item_without_moved_at_round_trips_unchanged() -> None:
    text = (
        "---\nlevel: story\nstatus: doing\ngate: ''\n"
        "children: []\nrealizes: []\n---\nLegacy work.\n"
    )
    item = parse_workitem(text, item_id="WORK-001")
    assert item.moved_at == ""
    assert dump_workitem(item) == text


LEAF = """\
---
level: action
status: todo
gate: "pytest -q"
children: []
---
Add the endpoint and make its tests pass.
"""

CONTAINER = """\
---
level: story
status: todo
gate: ""
children:
  - ACT-001
  - ACT-002
---
Stand up the endpoint.
"""

UNPLANNED = """\
---
level: initiative
status: todo
gate: ""
children: []
---
Stand up auth.
"""

OLD_LEAF = """\
---
level: action
status: todo
gate: pytest -q
children: []
realizes:
- feature/login
---
Build login.
"""

OLD_CONTAINER = """\
---
level: story
status: doing
gate: ''
children:
- ACT-001
- ACT-002
realizes: []
---
Ship auth.
"""


@pytest.mark.parametrize(
    ("status", "gate", "children", "accept", "gate_passed"),
    [
        ("todo", "pytest -q", [], "gate", False),
        ("doing", "pytest -q", [], "gate", False),
        ("done", "pytest -q", [], "gate", True),
        ("todo", "", ["ACT-001"], "children", False),
        ("done", "", ["ACT-001"], "children", False),
        ("todo", "", [], "person", False),
        ("done", "", [], "person", False),
        ("doing", "", ["ACT-001"], "children", False),
    ],
)
def test_every_legacy_shape_and_status_keeps_its_bytes(
    status: str,
    gate: str,
    children: list[str],
    accept: str,
    gate_passed: bool,
) -> None:
    gate_yaml = f"gate: {gate}" if gate else "gate: ''"
    children_yaml = "children: []" if not children else "children:\n- ACT-001"
    text = (
        f"---\nlevel: work\nstatus: {status}\n{gate_yaml}\n{children_yaml}\n"
        "realizes: []\n---\nLegacy goal.\n"
    )

    item = parse_workitem(text, item_id="WORK-001")

    assert item.accept == accept
    assert item.phase == ""
    assert item.phase_note == ""
    assert item.judgments == []
    assert item.gate_passed is gate_passed
    assert dump_workitem(item) == text


@pytest.mark.parametrize("status", ["review", "rework", "cancelled"])
def test_new_statuses_round_trip(status: str) -> None:
    item = WorkItem(
        id="ACT-001",
        level="action",
        status=status,
        gate="",
        children=[],
        goal="Judge it.",
        accept="person",
    )

    assert parse_workitem(dump_workitem(item), item_id=item.id) == item


def test_accept_shape_validation() -> None:
    fields = {
        "id": "ACT-001",
        "level": "action",
        "status": "todo",
        "children": [],
        "goal": "Do it.",
    }

    with pytest.raises(ValidationError, match="accept.*gate"):
        WorkItem(**fields, gate="", accept="gate")
    with pytest.raises(ValidationError, match="accept.*children"):
        WorkItem(**fields, gate="true", accept="children")


def test_new_fields_are_written_only_when_they_are_meaningful() -> None:
    item = WorkItem(
        id="ACT-001",
        level="action",
        status="review",
        gate="true",
        children=[],
        goal="Judge it.",
        accept="person",
        phase="executing",
        phase_note="One edge case remains.",
        judgments=[{"action": "reject", "reason": "Try again", "at": "2026-10-05T00:00:00Z"}],
        gate_passed=True,
    )

    dumped = dump_workitem(item)

    assert "accept: person" in dumped
    assert "phase: executing" in dumped
    assert "phase_note: One edge case remains." in dumped
    assert "judgments:" in dumped
    assert "gate_passed: true" in dumped


def test_parse_leaf() -> None:
    item = parse_workitem(LEAF, item_id="ACT-001")
    assert isinstance(item, WorkItem)
    assert item.id == "ACT-001"
    assert item.level == "action"
    assert item.gate == "pytest -q"
    assert item.children == []
    assert item.is_leaf is True
    assert item.is_container is False


def test_parse_container() -> None:
    item = parse_workitem(CONTAINER, item_id="STORY-001")
    assert item.children == ["ACT-001", "ACT-002"]
    assert item.gate == ""
    assert item.is_container is True
    assert item.is_leaf is False


def test_parse_unplanned_item_is_neither() -> None:
    item = parse_workitem(UNPLANNED, item_id="INIT-001")
    assert item.is_leaf is False
    assert item.is_container is False
    assert item.level == "initiative"


def test_level_is_a_free_label() -> None:
    text = '---\nlevel: theme\nstatus: todo\ngate: ""\nchildren: []\n---\nBig theme.\n'
    assert parse_workitem(text, item_id="X").level == "theme"


@pytest.mark.parametrize(
    "text",
    [
        "no frontmatter\n",
        '---\nstatus: todo\ngate: ""\nchildren: []\n---\nb\n',  # missing level
        '---\nlevel: action\ngate: "x"\nchildren: []\n---\nb\n',  # missing status
        '---\nlevel: action\nstatus: nope\ngate: "x"\nchildren: []\n---\nb\n',  # bad status
        '---\nlevel: s\nstatus: todo\ngate: "x"\nchildren: [ACT-1]\n---\nb\n',  # both
        '---\nlevel: s\nstatus: todo\ngate: ""\nchildren: "ACT-1"\n---\nb\n',  # not list
        '---\nlevel: s\nstatus: todo\ngate: ""\nchildren: [1]\n---\nb\n',  # child not str
        '---\nlevel: s\nstatus: todo\ngate: ""\nchildren: []\nextra: x\n---\nb\n',  # unknown
        '---\nlevel: s\nstatus: todo\ngate: ""\nchildren: []\n---\n\n',  # empty goal
    ],
)
def test_rejects_malformed(text: str) -> None:
    with pytest.raises(FormatError):
        parse_workitem(text, item_id="X")


def test_round_trips_leaf_and_container() -> None:
    leaf = parse_workitem(LEAF, item_id="ACT-001")
    assert parse_workitem(dump_workitem(leaf), item_id="ACT-001") == leaf
    box = parse_workitem(CONTAINER, item_id="STORY-001")
    assert parse_workitem(dump_workitem(box), item_id="STORY-001") == box


@pytest.mark.parametrize(
    ("text", "item_id"),
    [(OLD_LEAF, "ACT-001"), (OLD_CONTAINER, "STORY-001")],
)
def test_old_workitem_round_trips_byte_for_byte(text: str, item_id: str) -> None:
    item = parse_workitem(text, item_id=item_id)
    assert item.after == []
    assert dump_workitem(item) == text


def test_after_round_trips_after_realizes() -> None:
    text = """\
---
level: action
status: todo
gate: pytest -q
children: []
realizes: []
after:
- ACT-001
- STORY-002
---
Build login.
"""
    item = parse_workitem(text, item_id="ACT-003")
    assert item.after == ["ACT-001", "STORY-002"]
    dumped = dump_workitem(item)
    assert dumped.index("realizes:") < dumped.index("after:")
    assert parse_workitem(dumped, item_id=item.id) == item


@pytest.mark.parametrize(
    "after_yaml",
    [
        "after: [ACT-001, ACT-001]",
        "after: [ACT-002]",
        "after: ['']",
        "after: ['   ']",
        "after: ACT-001",
        "after: [1]",
    ],
)
def test_rejects_invalid_after(after_yaml: str) -> None:
    text = (
        "---\nlevel: action\nstatus: todo\ngate: pytest -q\nchildren: []\n"
        f"realizes: []\n{after_yaml}\n---\nBuild login.\n"
    )
    with pytest.raises(FormatError, match="after"):
        parse_workitem(text, item_id="ACT-002")
