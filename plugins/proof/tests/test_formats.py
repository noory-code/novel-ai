"""The Decision file format — frontmatter (machine) + body (prose).

Identity is the file name, not a frontmatter field. A decision records its
title, status, and what it supersedes; the body holds context / decision /
alternatives / consequences as free Markdown.
"""

import pytest

from proof.errors import FormatError
from proof.formats import Decision, dump_decision, parse_decision

ACCEPTED = """\
---
title: Use Postgres for the primary store
status: accepted
supersedes: null
---
## Decision
We will use Postgres.
"""

SUPERSEDING = """\
---
title: Move to CockroachDB
status: accepted
supersedes: PROOF-001
---
## Decision
Replace Postgres with CockroachDB for multi-region.
"""


def test_parse_accepted_decision() -> None:
    dec = parse_decision(ACCEPTED, decision_id="PROOF-001")
    assert isinstance(dec, Decision)
    assert dec.id == "PROOF-001"
    assert dec.title == "Use Postgres for the primary store"
    assert dec.status == "accepted"
    assert dec.supersedes is None
    assert dec.body.startswith("## Decision")


def test_parse_superseding_decision() -> None:
    dec = parse_decision(SUPERSEDING, decision_id="PROOF-002")
    assert dec.supersedes == "PROOF-001"


def test_proposed_status_allowed() -> None:
    text = "---\ntitle: Maybe Redis\nstatus: proposed\nsupersedes: null\n---\nAn option.\n"
    assert parse_decision(text, decision_id="PROOF-003").status == "proposed"


@pytest.mark.parametrize(
    "text",
    [
        "no frontmatter\n",
        "---\nstatus: accepted\nsupersedes: null\n---\nb\n",  # missing title
        "---\ntitle: x\nsupersedes: null\n---\nb\n",  # missing status
        "---\ntitle: x\nstatus: maybe\nsupersedes: null\n---\nb\n",  # bad status
        "---\ntitle: x\nstatus: accepted\nsupersedes: 5\n---\nb\n",  # supersedes wrong type
        "---\ntitle: x\nstatus: accepted\nsupersedes: null\nextra: y\n---\nb\n",  # unknown field
        "---\ntitle: x\nstatus: accepted\nsupersedes: null\n---\n\n",  # empty body
    ],
)
def test_rejects_malformed(text: str) -> None:
    with pytest.raises(FormatError):
        parse_decision(text, decision_id="X")


def test_round_trips() -> None:
    for text, did in ((ACCEPTED, "PROOF-001"), (SUPERSEDING, "PROOF-002")):
        dec = parse_decision(text, decision_id=did)
        assert parse_decision(dump_decision(dec), decision_id=did) == dec


def test_about_tags_parsed_and_round_trip() -> None:
    text = (
        "---\ntitle: Use Postgres\nstatus: accepted\nsupersedes: null\n"
        "about:\n  - ACT-005\n  - feature/login\n---\n## Decision\nPostgres.\n"
    )
    dec = parse_decision(text, decision_id="PROOF-001")
    assert dec.about == ["ACT-005", "feature/login"]
    assert parse_decision(dump_decision(dec), decision_id="PROOF-001") == dec


def test_about_defaults_empty() -> None:
    assert parse_decision(ACCEPTED, decision_id="PROOF-001").about == []
