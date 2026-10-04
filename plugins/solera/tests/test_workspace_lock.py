"""Cross-process serialization for workspace read-modify-write operations."""

from __future__ import annotations

import multiprocessing
import re
from pathlib import Path
from time import sleep
from typing import Any

import pytest

from solera.audit import audit_workspace
from solera.errors import WorkspaceLockTimeoutError
from solera.formats import WorkItem
from solera.intake import has_imported_design
from solera.planning import create_item
from solera.supervisor import start_next
from solera.workspace import Workspace


def _create_children_with_slow_first_write(root: str, barrier: Any, count: int) -> None:
    """Race child creation after widening its item/parent write window."""
    ws = Workspace(Path(root))
    original_write_item = Workspace.write_item

    def slow_write_item(self: Workspace, item: WorkItem) -> None:
        original_write_item(self, item)
        if item.id.startswith("ACT-"):
            sleep(0.02)

    setattr(Workspace, "write_item", slow_write_item)
    barrier.wait()
    for index in range(count):
        create_item(ws, "action", f"child {index}", gate="true", parent="STORY-001")


def _hold_workspace_lock(root: str, ready: Any, release: Any) -> None:
    ws = Workspace(Path(root))
    with ws.lock():
        ready.set()
        release.wait(5)


def test_two_processes_do_not_lose_children(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")
    parent = create_item(ws, "story", "parent")
    child_count = 5
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(3)
    processes = [
        context.Process(
            target=_create_children_with_slow_first_write,
            args=(str(ws.root), barrier, child_count),
        )
        for _ in range(2)
    ]

    for process in processes:
        process.start()
    barrier.wait()
    for process in processes:
        process.join(timeout=10)

    assert [process.exitcode for process in processes] == [0, 0]
    children = ws.load_item(parent.id).children
    assert len(children) == 2 * child_count
    assert len(set(children)) == len(children)
    assert all(ws.item_path(item_id).is_file() for item_id in children)


def test_locked_operation_can_call_another_locked_operation(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")
    leaf = create_item(ws, "action", "do it", gate="true")

    assert start_next(ws) == leaf.id
    assert ws.load_item(leaf.id).status == "doing"


def test_lock_file_is_not_workspace_data(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")

    with ws.lock():
        pass

    assert ws.lock_path.is_file()
    assert ws.list_items() == []
    assert has_imported_design(ws) is False
    assert audit_workspace(ws) == []


def test_workspace_lock_times_out_when_another_process_holds_it(tmp_path: Path) -> None:
    ws = Workspace(tmp_path / ".noory" / "solera")
    context = multiprocessing.get_context("spawn")
    ready = context.Event()
    release = context.Event()
    holder = context.Process(target=_hold_workspace_lock, args=(str(ws.root), ready, release))
    holder.start()
    assert ready.wait(5)

    try:
        with pytest.raises(WorkspaceLockTimeoutError, match=re.escape(str(ws.root / ".lock"))):
            with ws.lock(timeout=0.1):
                pytest.fail("lock unexpectedly acquired")
    finally:
        release.set()
        holder.join(timeout=5)

    assert holder.exitcode == 0
