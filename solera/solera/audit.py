"""Cross-file workspace audit — the capstone guard.

Per-file parsing fails fast on its own (CORE-1). This audit checks the relations
*between* files: every referenced Action has a parseable file, no Action file is
orphaned, and the ``progress.md`` pointer points at things that exist. It
collects problems and returns them rather than raising, so a caller can report
every issue at once instead of stopping at the first.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import FormatError
from .workspace import Workspace

_RESERVED = {"story.md", "RETROSPECTIVE.md"}


@dataclass(frozen=True)
class Problem:
    """One integrity problem found by the audit."""

    kind: str
    detail: str


def audit_workspace(ws: Workspace) -> list[Problem]:
    """Return every referential-integrity problem in the workspace (possibly empty)."""
    problems: list[Problem] = []

    for story_id in ws.list_stories():
        try:
            story = ws.load_story(story_id)
        except FormatError as exc:
            problems.append(
                Problem("malformed-story", f"{story_id}: cannot parse story.md ({exc})")
            )
            continue

        referenced = set(story.actions)
        for action_id in story.actions:
            if not ws.action_path(story_id, action_id).exists():
                problems.append(
                    Problem(
                        "missing-action",
                        f"{story_id}/{action_id}: referenced action file is missing",
                    )
                )
                continue
            try:
                ws.load_action(story_id, action_id)
            except FormatError as exc:
                problems.append(
                    Problem("malformed-action", f"{story_id}/{action_id}: cannot parse ({exc})")
                )

        for path in sorted(ws.story_dir(story_id).glob("*.md")):
            if path.name not in _RESERVED and path.stem not in referenced:
                problems.append(
                    Problem(
                        "orphan-action",
                        f"{story_id}/{path.stem}: orphan action file not referenced by its story",
                    )
                )

    problems.extend(_audit_pointer(ws))
    return problems


def _audit_pointer(ws: Workspace) -> list[Problem]:
    if not ws.progress_path.exists():
        return []
    try:
        prog = ws.load_progress()
    except FormatError as exc:
        return [Problem("malformed-progress", f"progress.md: cannot parse ({exc})")]

    stories = set(ws.list_stories())
    if prog.story is not None and prog.story not in stories:
        return [
            Problem(
                "dangling-pointer",
                f"progress points at story {prog.story} which does not exist",
            )
        ]
    if prog.story is not None and prog.action is not None:
        story = ws.load_story(prog.story)
        if prog.action not in story.actions:
            return [
                Problem(
                    "dangling-pointer",
                    f"progress points at action {prog.action} not in {prog.story}",
                )
            ]
    return []
