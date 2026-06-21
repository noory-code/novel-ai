"""Layout of and read access to a ``.noory/solera/`` workspace.

``Workspace`` is the single entry point for every path and every read. Identity
lives in the path: a Story id is its directory name, an Action id is its file
stem. Reads go through :mod:`solera.formats`, so a malformed file raises
:class:`~solera.errors.FormatError` here rather than corrupting later steps.
"""

from __future__ import annotations

from pathlib import Path

from .formats import (
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


class Workspace:
    """A ``.noory/solera/`` directory addressed through composed paths."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    # --- paths -------------------------------------------------------------

    @property
    def progress_path(self) -> Path:
        return self.root / "progress.md"

    @property
    def stories_dir(self) -> Path:
        return self.root / "stories"

    def story_dir(self, story_id: str) -> Path:
        return self.stories_dir / story_id

    def story_path(self, story_id: str) -> Path:
        return self.story_dir(story_id) / "story.md"

    def action_path(self, story_id: str, action_id: str) -> Path:
        return self.story_dir(story_id) / f"{action_id}.md"

    # --- reads -------------------------------------------------------------

    def load_progress(self) -> Progress:
        return parse_progress(self.progress_path.read_text())

    def load_story(self, story_id: str) -> Story:
        return parse_story(self.story_path(story_id).read_text(), story_id=story_id)

    def load_action(self, story_id: str, action_id: str) -> Action:
        text = self.action_path(story_id, action_id).read_text()
        return parse_action(text, action_id=action_id)

    def list_stories(self) -> list[str]:
        if not self.stories_dir.is_dir():
            return []
        return sorted(p.name for p in self.stories_dir.iterdir() if p.is_dir())

    # --- writes ------------------------------------------------------------

    def write_progress(self, progress: Progress) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.progress_path.write_text(dump_progress(progress))

    def write_story(self, story: Story) -> None:
        self.story_dir(story.id).mkdir(parents=True, exist_ok=True)
        self.story_path(story.id).write_text(dump_story(story))

    def write_action(self, story_id: str, action: Action) -> None:
        self.story_dir(story_id).mkdir(parents=True, exist_ok=True)
        self.action_path(story_id, action.id).write_text(dump_action(action))
