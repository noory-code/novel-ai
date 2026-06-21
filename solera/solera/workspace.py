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
    Feedback,
    Progress,
    Retrospective,
    Story,
    dump_action,
    dump_feedback,
    dump_progress,
    dump_retrospective,
    dump_story,
    parse_action,
    parse_feedback,
    parse_progress,
    parse_retrospective,
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

    def retrospective_path(self, story_id: str) -> Path:
        return self.story_dir(story_id) / "RETROSPECTIVE.md"

    @property
    def feedback_dir(self) -> Path:
        return self.root / "feedback"

    def feedback_path(self, feedback_id: str) -> Path:
        return self.feedback_dir / f"{feedback_id}.md"

    # --- reads -------------------------------------------------------------

    def load_progress(self) -> Progress:
        return parse_progress(self.progress_path.read_text())

    def load_story(self, story_id: str) -> Story:
        return parse_story(self.story_path(story_id).read_text(), story_id=story_id)

    def load_action(self, story_id: str, action_id: str) -> Action:
        text = self.action_path(story_id, action_id).read_text()
        return parse_action(text, action_id=action_id)

    def load_retrospective(self, story_id: str) -> Retrospective:
        text = self.retrospective_path(story_id).read_text()
        return parse_retrospective(text, story_id=story_id)

    def load_feedback(self, feedback_id: str) -> Feedback:
        text = self.feedback_path(feedback_id).read_text()
        return parse_feedback(text, feedback_id=feedback_id)

    def list_stories(self) -> list[str]:
        if not self.stories_dir.is_dir():
            return []
        return sorted(p.name for p in self.stories_dir.iterdir() if p.is_dir())

    def list_feedback(self) -> list[str]:
        if not self.feedback_dir.is_dir():
            return []
        return sorted(p.stem for p in self.feedback_dir.glob("*.md"))

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

    def write_retrospective(self, retro: Retrospective) -> None:
        self.story_dir(retro.id).mkdir(parents=True, exist_ok=True)
        self.retrospective_path(retro.id).write_text(dump_retrospective(retro))

    def write_feedback(self, feedback: Feedback) -> None:
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.feedback_path(feedback.id).write_text(dump_feedback(feedback))
