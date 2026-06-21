"""D2-2 — the recursive WorkItem: one node type for the whole altitude ladder.

A WorkItem is any rung — initiative, epic, story, or action. ``level`` is a free
label (the conventional ladder is initiative/epic/story/action). The invariant
that keeps the tree executable: a leaf carries a ``gate`` and no children; a
container carries children and no gate. An item may have neither yet (a
container awaiting decomposition), but never both — it cannot be leaf and
container at once.
"""

import pytest

from solera.errors import FormatError
from solera.formats import WorkItem, dump_workitem, parse_workitem

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
    text = "---\nlevel: theme\nstatus: todo\ngate: \"\"\nchildren: []\n---\nBig theme.\n"
    assert parse_workitem(text, item_id="X").level == "theme"


@pytest.mark.parametrize(
    "text",
    [
        "no frontmatter\n",
        "---\nstatus: todo\ngate: \"\"\nchildren: []\n---\nb\n",  # missing level
        "---\nlevel: action\ngate: \"x\"\nchildren: []\n---\nb\n",  # missing status
        "---\nlevel: action\nstatus: nope\ngate: \"x\"\nchildren: []\n---\nb\n",  # bad status
        "---\nlevel: s\nstatus: todo\ngate: \"x\"\nchildren: [ACT-1]\n---\nb\n",  # both
        "---\nlevel: s\nstatus: todo\ngate: \"\"\nchildren: \"ACT-1\"\n---\nb\n",  # not list
        "---\nlevel: s\nstatus: todo\ngate: \"\"\nchildren: [1]\n---\nb\n",  # child not str
        "---\nlevel: s\nstatus: todo\ngate: \"\"\nchildren: []\nextra: x\n---\nb\n",  # unknown
        "---\nlevel: s\nstatus: todo\ngate: \"\"\nchildren: []\n---\n\n",  # empty goal
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
