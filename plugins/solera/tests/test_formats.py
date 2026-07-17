"""The progress pointer parse/dump.

(WorkItem is covered in test_workitem; notes in test_retro_feedback.)
"""

import pytest
from pydantic import ValidationError

from solera.errors import FormatError
from solera.formats import WorkItem, dump_progress, parse_progress


def test_workitem_rejects_blank_gate_but_accepts_empty_and_real_gates() -> None:
    fields = {"id": "ACT-001", "level": "action", "status": "todo", "goal": "Do it."}

    with pytest.raises(ValidationError, match="gate must not be blank"):
        WorkItem(**fields, gate="   ")

    assert WorkItem(**fields, gate="").is_leaf is False
    assert WorkItem(**fields, gate="pytest -q").is_leaf is True


def test_parse_progress_reads_item() -> None:
    assert parse_progress("---\nitem: ACT-001\n---\n").item == "ACT-001"


def test_parse_progress_allows_null() -> None:
    assert parse_progress("---\nitem: null\n---\n").item is None


@pytest.mark.parametrize(
    "text",
    [
        "no frontmatter\n",
        "---\n---\n",  # missing item key
        "---\nitem: 5\n---\n",  # wrong type
        "---\nitem: A\nextra: x\n---\n",  # unknown field
    ],
)
def test_parse_progress_rejects_malformed(text: str) -> None:
    with pytest.raises(FormatError):
        parse_progress(text)


@pytest.mark.parametrize("text", ["---\nitem: ACT-001\n---\n", "---\nitem: null\n---\n"])
def test_progress_round_trips(text: str) -> None:
    prog = parse_progress(text)
    assert parse_progress(dump_progress(prog)) == prog
