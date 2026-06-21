"""Layout of and access to a ``.noory/solera/`` workspace.

``Workspace`` is the single entry point for every path and every read/write.
Work is a flat set of :class:`~solera.formats.WorkItem` files under ``items/``;
the tree is reconstructed from each item's ``children`` list (storage stays flat
so re-parenting and arbitrary depth cost nothing). Identity lives in the path: an
item's id is its file stem. Retrospectives and artifacts attach to any item by
that id.
"""

from __future__ import annotations

from pathlib import Path

from .formats import (
    Feedback,
    Progress,
    Retrospective,
    WorkItem,
    dump_feedback,
    dump_progress,
    dump_retrospective,
    dump_workitem,
    parse_feedback,
    parse_progress,
    parse_retrospective,
    parse_workitem,
)


class Workspace:
    """A ``.noory/solera/`` directory addressed through composed paths."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    # --- paths -------------------------------------------------------------

    @property
    def progress_path(self) -> Path:
        return self.root / "progress.md"

    @property
    def items_dir(self) -> Path:
        return self.root / "items"

    def item_path(self, item_id: str) -> Path:
        return self.items_dir / f"{item_id}.md"

    def retrospective_path(self, item_id: str) -> Path:
        return self.root / "retros" / f"{item_id}.md"

    def artifacts_dir(self, item_id: str) -> Path:
        return self.root / "artifacts" / item_id

    @property
    def feedback_dir(self) -> Path:
        return self.root / "feedback"

    def feedback_path(self, feedback_id: str) -> Path:
        return self.feedback_dir / f"{feedback_id}.md"

    # --- reads -------------------------------------------------------------

    def load_progress(self) -> Progress:
        return parse_progress(self.progress_path.read_text())

    def load_item(self, item_id: str) -> WorkItem:
        return parse_workitem(self.item_path(item_id).read_text(), item_id=item_id)

    def load_retrospective(self, item_id: str) -> Retrospective:
        return parse_retrospective(self.retrospective_path(item_id).read_text(), item_id=item_id)

    def load_feedback(self, feedback_id: str) -> Feedback:
        return parse_feedback(self.feedback_path(feedback_id).read_text(), feedback_id=feedback_id)

    def list_items(self) -> list[str]:
        if not self.items_dir.is_dir():
            return []
        return sorted(p.stem for p in self.items_dir.glob("*.md"))

    def list_feedback(self) -> list[str]:
        if not self.feedback_dir.is_dir():
            return []
        return sorted(p.stem for p in self.feedback_dir.glob("*.md"))

    # --- writes ------------------------------------------------------------

    def write_progress(self, progress: Progress) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.progress_path.write_text(dump_progress(progress))

    def write_item(self, item: WorkItem) -> None:
        self.items_dir.mkdir(parents=True, exist_ok=True)
        self.item_path(item.id).write_text(dump_workitem(item))

    def write_retrospective(self, retro: Retrospective) -> None:
        self.retrospective_path(retro.id).parent.mkdir(parents=True, exist_ok=True)
        self.retrospective_path(retro.id).write_text(dump_retrospective(retro))

    def write_feedback(self, feedback: Feedback) -> None:
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_path(feedback.id).write_text(dump_feedback(feedback))
