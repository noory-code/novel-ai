"""CORE-6 — retrospective (after work) and feedback (while blocked).

Both are neutral ID-tagged notes. The ``about`` tag is optional: standalone
Solera has no published spec to point at, so a retrospective or feedback note
works with an empty tag list and still parses. When Plot is connected the tag
carries ids like ``feature/login@v2`` — but that is an integration concern, not
a core requirement.
"""

from pathlib import Path

import pytest

from solera.errors import FormatError
from solera.formats import (
    Feedback,
    Retrospective,
    dump_feedback,
    dump_retrospective,
    parse_feedback,
    parse_retrospective,
)
from solera.workspace import Workspace

# --- retrospective ---------------------------------------------------------


def test_parse_retrospective_reads_body_and_tags() -> None:
    text = "---\nabout:\n  - feature/login\n---\nThe design missed the error path.\n"
    retro = parse_retrospective(text, story_id="STORY-001")
    assert isinstance(retro, Retrospective)
    assert retro.id == "STORY-001"
    assert retro.about == ["feature/login"]
    assert retro.body == "The design missed the error path."


def test_parse_retrospective_allows_empty_tags_standalone() -> None:
    retro = parse_retrospective("---\n---\nWhat we learned.\n", story_id="STORY-002")
    assert retro.about == []


@pytest.mark.parametrize(
    "text",
    [
        "no frontmatter\n",
        "---\nabout: feature/login\n---\nbody\n",  # about not a list
        "---\nabout: [1]\n---\nbody\n",  # tag not a string
        "---\nextra: x\n---\nbody\n",  # unknown field
        "---\n---\n\n",  # empty body
    ],
)
def test_parse_retrospective_rejects_malformed(text: str) -> None:
    with pytest.raises(FormatError):
        parse_retrospective(text, story_id="STORY-XXX")


# --- feedback --------------------------------------------------------------


def test_parse_feedback_reads_body_and_tags() -> None:
    text = "---\nabout:\n  - feature/login@v2\n---\nBlocked: spec is ambiguous.\n"
    fb = parse_feedback(text, feedback_id="FB-001")
    assert isinstance(fb, Feedback)
    assert fb.id == "FB-001"
    assert fb.about == ["feature/login@v2"]
    assert fb.body == "Blocked: spec is ambiguous."


def test_parse_feedback_allows_empty_tags() -> None:
    fb = parse_feedback("---\n---\nStuck on a missing tool.\n", feedback_id="FB-002")
    assert fb.about == []


# --- round-trips + workspace io --------------------------------------------


def test_retrospective_round_trips() -> None:
    retro = parse_retrospective("---\nabout: [a, b]\n---\nLearned.\n", story_id="S1")
    assert parse_retrospective(dump_retrospective(retro), story_id="S1") == retro


def test_feedback_round_trips() -> None:
    fb = parse_feedback("---\nabout: [x]\n---\nNote.\n", feedback_id="FB-1")
    assert parse_feedback(dump_feedback(fb), feedback_id="FB-1") == fb


def test_workspace_writes_and_loads_retrospective(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")
    ws.story_dir("STORY-001").mkdir(parents=True)
    retro = Retrospective(id="STORY-001", about=[], body="Done; learned X.")
    ws.write_retrospective(retro)
    assert ws.retrospective_path("STORY-001").exists()
    assert ws.load_retrospective("STORY-001") == retro


def test_workspace_writes_and_loads_feedback(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")
    fb = Feedback(id="FB-001", about=["feature/login"], body="Blocked.")
    ws.write_feedback(fb)
    assert ws.feedback_path("FB-001").exists()
    assert ws.load_feedback("FB-001") == fb
    assert ws.list_feedback() == ["FB-001"]
