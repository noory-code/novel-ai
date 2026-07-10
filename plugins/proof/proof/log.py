"""The append-only decision log over ``.noory/proof/``.

A :class:`Log` records decisions and never edits them. Each ``record`` writes a
new immutable file; to change a decision you record a new one that supersedes the
old. Whether a decision is *in force* is derived, not stored: it is in force when
it is ``accepted`` and no accepted decision supersedes it.
"""

from __future__ import annotations

import re
from pathlib import Path

from .formats import Decision, Status, dump_decision, parse_decision

_ID_RE = re.compile(r"^PROOF-(\d+)$")


class Log:
    """A ``.noory/proof/`` directory of decision files."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def decision_path(self, decision_id: str) -> Path:
        return self.root / f"{decision_id}.md"

    def list_ids(self) -> list[str]:
        if not self.root.is_dir():
            return []
        return sorted(p.stem for p in self.root.glob("*.md") if _ID_RE.match(p.stem))

    def get(self, decision_id: str) -> Decision:
        return parse_decision(self.decision_path(decision_id).read_text(), decision_id=decision_id)

    def decisions(self) -> list[Decision]:
        return [self.get(decision_id) for decision_id in self.list_ids()]

    def next_id(self) -> str:
        highest = 0
        for decision_id in self.list_ids():
            match = _ID_RE.match(decision_id)
            if match:
                highest = max(highest, int(match.group(1)))
        return f"PROOF-{highest + 1:03d}"

    def record(
        self,
        title: str,
        body: str,
        *,
        status: Status = "accepted",
        supersedes: str | None = None,
        about: list[str] | None = None,
    ) -> Decision:
        """Append a new decision and return it. Never edits an existing one."""
        decision = Decision(
            id=self.next_id(),
            title=title,
            status=status,
            supersedes=supersedes,
            about=about or [],
            body=body,
        )
        self.root.mkdir(parents=True, exist_ok=True)
        self.decision_path(decision.id).write_text(dump_decision(decision))
        return decision

    def in_force(self, *, about: str | None = None) -> list[Decision]:
        """Accepted decisions that no accepted decision supersedes (derived).

        ``about`` filters to decisions that tag the given id — the link a
        decision-type work-item's gate checks ("a decision about this leaf").
        """
        accepted = [d for d in self.decisions() if d.status == "accepted"]
        retired = {d.supersedes for d in accepted if d.supersedes is not None}
        standing = [d for d in accepted if d.id not in retired]
        if about is None:
            return standing
        return [d for d in standing if about in d.about]
