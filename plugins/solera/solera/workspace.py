"""Layout of and access to a ``.noory/solera/`` workspace.

``Workspace`` is the single entry point for every path and every read/write.
Work is a flat set of :class:`~solera.formats.WorkItem` files under ``items/``;
the tree is reconstructed from each item's ``children`` list (storage stays flat
so re-parenting and arbitrary depth cost nothing). Identity lives in the path: an
item's id is its file stem. Retrospectives and artifacts attach to any item by
that id.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import threading
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from time import monotonic, sleep
from typing import BinaryIO, Concatenate, ParamSpec, TypeVar, cast

from .errors import FormatError, WorkspaceLockTimeoutError
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

_PATH_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
DEFAULT_LOCK_TIMEOUT_SECONDS = 10.0
_LOCK_POLL_SECONDS = 0.05
_P = ParamSpec("_P")
_R = TypeVar("_R")


if sys.platform == "win32":
    import msvcrt

    def _try_file_lock(handle: BinaryIO) -> bool:
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return False
        return True

    def _release_file_lock(handle: BinaryIO) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _try_file_lock(handle: BinaryIO) -> bool:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        return True

    def _release_file_lock(handle: BinaryIO) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


@dataclass
class _LockState:
    mutex: threading.RLock = field(default_factory=threading.RLock)
    depth: int = 0
    handle: BinaryIO | None = None


_lock_states: dict[str, _LockState] = {}
_lock_states_mutex = threading.Lock()


def _lock_state(path: Path) -> _LockState:
    key = os.path.normcase(str(path.resolve(strict=False)))
    with _lock_states_mutex:
        return _lock_states.setdefault(key, _LockState())


def _timeout_error(path: Path, timeout: float) -> WorkspaceLockTimeoutError:
    return WorkspaceLockTimeoutError(
        f"timed out after {timeout:g} seconds acquiring workspace lock {path}"
    )


def _atomic_write_text(path: Path, text: str) -> None:
    """Write text beside its destination, then atomically replace the file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        temporary_path.write_text(text)
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def validate_path_name(name: str) -> str:
    """Return a safe single path component or reject it before path composition."""
    if not _PATH_NAME_RE.fullmatch(name) or name == "..":
        raise FormatError(
            f"invalid path name {name!r}: expected a single component matching "
            "^[A-Za-z0-9][A-Za-z0-9._-]*$"
        )
    return name


class Workspace:
    """A ``.noory/solera/`` directory addressed through composed paths."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    # --- paths -------------------------------------------------------------

    @property
    def progress_path(self) -> Path:
        return self.root / "progress.md"

    @property
    def lock_path(self) -> Path:
        return self.root / ".lock"

    @property
    def items_dir(self) -> Path:
        return self.root / "items"

    def item_path(self, item_id: str) -> Path:
        return self.items_dir / f"{validate_path_name(item_id)}.md"

    def retrospective_path(self, item_id: str) -> Path:
        return self.root / "retros" / f"{validate_path_name(item_id)}.md"

    def artifacts_dir(self, item_id: str) -> Path:
        return self.root / "artifacts" / validate_path_name(item_id)

    @property
    def feedback_dir(self) -> Path:
        return self.root / "feedback"

    @property
    def specs_dir(self) -> Path:
        """Imported format F bundles (the input spec) — `specs/{label}/`. Each
        import is a frozen copy, so Solera works against an immutable spec even
        if the upstream design moves (04-pipeline)."""
        return self.root / "specs"

    def spec_dir(self, label: str) -> Path:
        return self.specs_dir / validate_path_name(label)

    def feedback_path(self, feedback_id: str) -> Path:
        return self.feedback_dir / f"{validate_path_name(feedback_id)}.md"

    def lock(self, timeout: float = DEFAULT_LOCK_TIMEOUT_SECONDS) -> AbstractContextManager[None]:
        """Acquire this workspace's re-entrant cross-process exclusive lock."""
        return workspace_lock(self, timeout=timeout)

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
        _atomic_write_text(self.progress_path, dump_progress(progress))

    def write_item(self, item: WorkItem) -> None:
        _atomic_write_text(self.item_path(item.id), dump_workitem(item))

    def write_retrospective(self, retro: Retrospective) -> None:
        _atomic_write_text(self.retrospective_path(retro.id), dump_retrospective(retro))

    def write_feedback(self, feedback: Feedback) -> None:
        _atomic_write_text(self.feedback_path(feedback.id), dump_feedback(feedback))


@contextmanager
def workspace_lock(ws: Workspace, timeout: float = DEFAULT_LOCK_TIMEOUT_SECONDS) -> Iterator[None]:
    """Serialize a workspace operation across processes and threads."""
    if timeout < 0:
        raise ValueError("workspace lock timeout must be non-negative")
    deadline = monotonic() + timeout
    state = _lock_state(ws.lock_path)
    if not state.mutex.acquire(timeout=max(0.0, deadline - monotonic())):
        raise _timeout_error(ws.lock_path, timeout)

    try:
        if state.depth:
            state.depth += 1
        else:
            ws.root.mkdir(parents=True, exist_ok=True)
            acquired_handle = ws.lock_path.open("a+b")
            try:
                if acquired_handle.seek(0, os.SEEK_END) == 0:
                    acquired_handle.write(b"\0")
                    acquired_handle.flush()
                while not _try_file_lock(acquired_handle):
                    remaining = deadline - monotonic()
                    if remaining <= 0:
                        raise _timeout_error(ws.lock_path, timeout)
                    sleep(min(_LOCK_POLL_SECONDS, remaining))
            except BaseException:
                acquired_handle.close()
                raise
            state.handle = acquired_handle
            state.depth = 1

        try:
            yield
        finally:
            state.depth -= 1
            if state.depth == 0:
                release_handle = state.handle
                state.handle = None
                assert release_handle is not None
                try:
                    _release_file_lock(release_handle)
                finally:
                    release_handle.close()
    finally:
        state.mutex.release()


def workspace_locked(
    operation: Callable[Concatenate[Workspace, _P], _R],
) -> Callable[Concatenate[Workspace, _P], _R]:
    """Run one public workspace mutation while holding its workspace lock."""

    @wraps(operation)
    def wrapped(ws: Workspace, *args: _P.args, **kwargs: _P.kwargs) -> _R:
        with ws.lock():
            return operation(ws, *args, **kwargs)

    return cast(Callable[Concatenate[Workspace, _P], _R], wrapped)
