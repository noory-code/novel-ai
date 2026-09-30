"""Re-pin (INT-f) maps service and shared format-F changes onto work items.

Proposals are deterministic and read-only; a human approves a proposal ID
before ``apply_repin`` mutates any work state.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from solera.formats import WorkItem
from solera.intake import ImportedRelease
from solera.planning import create_item
from solera.repin import apply_repin, propose_repin, reopen_items
from solera.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    return Workspace(tmp_path / ".noory" / "solera")


def _release(
    release: str,
    *,
    service: str = "service/auth",
    based_on: str = "vP1",
    service_elements: list[dict[str, str]] | None = None,
    project_elements: list[dict[str, str]] | None = None,
    actors: list[str] | None = None,
    entities: list[str] | None = None,
) -> ImportedRelease:
    return {
        "service": {
            "service": service,
            "release": release,
            "based_on": based_on,
            "elements": service_elements
            if service_elements is not None
            else [{"id": service, "hash": "service-hash"}],
            "refs": {
                "anchors": {"core_values": [], "identity": []},
                "actors": actors or [],
                "entities": entities or [],
            },
        },
        "project": {
            "release": based_on,
            "elements": project_elements or [],
        },
    }


def test_propose_repin_maps_diff_to_realizing_items(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    a = create_item(ws, "action", "A", gate="true", realizes=["feature/login"])
    create_item(ws, "action", "B", gate="true", realizes=["service/auth"])
    c = create_item(ws, "action", "C", gate="true", realizes=["entity/old"])

    old = _release(
        "vS1",
        service_elements=[
            {"id": "feature/login", "hash": "a"},
            {"id": "service/auth", "hash": "b"},
            {"id": "entity/old", "hash": "c"},
        ],
    )
    new = _release(
        "vS2",
        service_elements=[
            {"id": "feature/login", "hash": "AAA"},
            {"id": "service/auth", "hash": "b"},
        ],
    )

    prop = propose_repin(ws, old, new)

    assert prop["stale"] == [a.id]
    assert prop["escalate"] == [c.id]


def test_proposal_id_is_stable_for_the_same_inputs(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    create_item(ws, "action", "A", gate="true", realizes=["feature/login"])
    old = _release(
        "vS1",
        service_elements=[
            {"id": "service/auth", "hash": "service"},
            {"id": "feature/login", "hash": "old"},
        ],
    )
    new = _release(
        "vS2",
        service_elements=[
            {"id": "service/auth", "hash": "service"},
            {"id": "feature/login", "hash": "new"},
        ],
    )

    first = propose_repin(ws, old, new)["proposal_id"]
    second = propose_repin(ws, old, new)["proposal_id"]

    assert first == second
    assert re.fullmatch(r"[0-9a-f]{64}", first)


def test_apply_repin_rejects_changed_proposal_without_writing(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    first = create_item(ws, "action", "A", gate="true", realizes=["feature/login"])
    ws.write_item(ws.load_item(first.id).model_copy(update={"status": "done"}))
    old = _release(
        "vS1",
        service_elements=[
            {"id": "service/auth", "hash": "service"},
            {"id": "feature/login", "hash": "old"},
        ],
    )
    new = _release(
        "vS2",
        service_elements=[
            {"id": "service/auth", "hash": "service"},
            {"id": "feature/login", "hash": "new"},
        ],
    )
    proposal_id = propose_repin(ws, old, new)["proposal_id"]

    second = create_item(ws, "action", "B", gate="true", realizes=["feature/login"])
    ws.write_item(ws.load_item(second.id).model_copy(update={"status": "done"}))
    before = {
        path.relative_to(ws.root): path.read_bytes()
        for path in ws.root.rglob("*")
        if path.is_file()
    }

    with pytest.raises(ValueError, match="proposal changed"):
        apply_repin(ws, old, new, proposal_id)

    after = {
        path.relative_to(ws.root): path.read_bytes()
        for path in ws.root.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_apply_repin_with_current_id_reopens_only_stale_items(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    stale = create_item(ws, "action", "Stale", gate="true", realizes=["feature/login"])
    escalated = create_item(ws, "action", "Escalated", gate="true", realizes=["entity/old"])
    for item in (stale, escalated):
        ws.write_item(ws.load_item(item.id).model_copy(update={"status": "done"}))
    old = _release(
        "vS1",
        service_elements=[
            {"id": "service/auth", "hash": "service"},
            {"id": "feature/login", "hash": "old"},
            {"id": "entity/old", "hash": "old"},
        ],
    )
    new = _release(
        "vS2",
        service_elements=[
            {"id": "service/auth", "hash": "service"},
            {"id": "feature/login", "hash": "new"},
        ],
    )
    proposal = propose_repin(ws, old, new)

    applied = apply_repin(ws, old, new, proposal["proposal_id"])

    assert applied["reopened"] == [stale.id]
    assert ws.load_item(stale.id).status == "todo"
    assert ws.load_item(escalated.id).status == "done"


def test_referenced_shared_change_stales_service_work(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    item = create_item(ws, "action", "Login", gate="true", realizes=["feature/login"])
    ws.write_item(ws.load_item(item.id).model_copy(update={"status": "done"}))
    service_elements = [
        {"id": "service/auth", "hash": "s"},
        {"id": "feature/login", "hash": "f"},
    ]
    old = _release(
        "vS1",
        service_elements=service_elements,
        project_elements=[{"id": "actor/user", "hash": "old"}],
    )
    new = _release(
        "vS2",
        based_on="vP2",
        service_elements=service_elements,
        project_elements=[{"id": "actor/user", "hash": "new"}],
        actors=["actor/user"],
    )

    prop = propose_repin(ws, old, new)

    assert prop["stale"] == [item.id]
    assert prop["shared_diff"]["changed"] == ["actor/user"]


def test_unreferenced_shared_change_does_not_stale_service_work(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    create_item(ws, "action", "Login", gate="true", realizes=["feature/login"])
    service_elements = [
        {"id": "service/auth", "hash": "s"},
        {"id": "feature/login", "hash": "f"},
    ]
    old = _release(
        "vS1",
        service_elements=service_elements,
        project_elements=[{"id": "actor/user", "hash": "old"}],
    )
    new = _release(
        "vS2",
        based_on="vP2",
        service_elements=service_elements,
        project_elements=[{"id": "actor/user", "hash": "new"}],
    )

    prop = propose_repin(ws, old, new)

    assert prop["stale"] == []
    assert prop["escalate"] == []


def test_refs_only_change_stales_service_work(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    item = create_item(ws, "action", "Login", gate="true", realizes=["feature/login"])
    service_elements = [
        {"id": "service/auth", "hash": "s"},
        {"id": "feature/login", "hash": "f"},
    ]
    project_elements = [{"id": "actor/user", "hash": "actor"}]
    old = _release("vS1", service_elements=service_elements, project_elements=project_elements)
    new = _release(
        "vS2",
        service_elements=service_elements,
        project_elements=project_elements,
        actors=["actor/user"],
    )

    prop = propose_repin(ws, old, new)

    assert prop["refs_changed"] is True
    assert prop["stale"] == [item.id]


def test_removed_shared_element_escalates_realizing_work(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    item = create_item(ws, "action", "Entity", gate="true", realizes=["entity/x"])
    old = _release(
        "vS1",
        project_elements=[{"id": "entity/x", "hash": "entity"}],
        entities=["entity/x"],
    )
    new = _release("vS2", based_on="vP2")

    prop = propose_repin(ws, old, new)

    assert prop["escalate"] == [item.id]
    assert prop["shared_diff"]["removed"] == ["entity/x"]


def test_repin_rejects_skipped_service_release(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="one step at a time"):
        propose_repin(_ws(tmp_path), _release("vS1"), _release("vS3"))


def test_repin_rejects_different_services(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="different services"):
        propose_repin(
            _ws(tmp_path),
            _release("vS1"),
            _release("vS2", service="service/billing"),
        )


def test_reintroduced_service_element_escalates_realizing_work(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    item = create_item(ws, "action", "Login", gate="true", realizes=["feature/login"])
    old = _release("vS2")
    new = _release(
        "vS3",
        service_elements=[
            {"id": "service/auth", "hash": "s"},
            {"id": "feature/login", "hash": "new"},
        ],
    )

    prop = propose_repin(ws, old, new)

    assert prop["escalate"] == [item.id]
    assert prop["stale"] == []


def test_reopen_items_sets_done_back_to_todo(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    leaf = create_item(ws, "action", "A", gate="true", realizes=["feature/login"])
    ws.write_item(ws.load_item(leaf.id).model_copy(update={"status": "done"}))
    reopen_items(ws, [leaf.id])
    assert ws.load_item(leaf.id).status == "todo"


def test_reopen_invalidates_done_ancestors(tmp_path: Path) -> None:
    """Reopening a leaf must break its ancestors' ``done`` rollup."""
    from solera.supervisor import complete, start_next

    ws = _ws(tmp_path)
    story = create_item(ws, "story", "S")
    leaf = create_item(ws, "action", "A", gate="true", realizes=["feature/login"], parent=story.id)
    start_next(ws)
    assert complete(ws, leaf.id, cwd=tmp_path).passed is True
    assert ws.load_item(story.id).status == "done"

    reopen_items(ws, [leaf.id])
    assert ws.load_item(leaf.id).status == "todo"
    assert ws.load_item(story.id).status != "done"


def test_reopen_validates_every_target_before_writing(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    story = create_item(ws, "story", "S")
    leaf = create_item(ws, "action", "A", gate="true", parent=story.id)
    ws.write_item(ws.load_item(leaf.id).model_copy(update={"status": "done"}))
    ws.write_item(ws.load_item(story.id).model_copy(update={"status": "done"}))
    before = {path: path.read_bytes() for path in ws.items_dir.iterdir()}

    with pytest.raises(FileNotFoundError):
        reopen_items(ws, [leaf.id, "ACT-404"])

    assert {path: path.read_bytes() for path in ws.items_dir.iterdir()} == before


def test_reopen_writes_ancestors_before_leaf_and_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ws = _ws(tmp_path)
    story = create_item(ws, "story", "S")
    leaf = create_item(ws, "action", "A", gate="true", parent=story.id)
    ws.write_item(ws.load_item(leaf.id).model_copy(update={"status": "done"}))
    ws.write_item(ws.load_item(story.id).model_copy(update={"status": "done"}))
    original_write_item = ws.write_item
    calls = 0

    def fail_second_write(item: WorkItem) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("interrupted write")
        original_write_item(item)

    monkeypatch.setattr(ws, "write_item", fail_second_write)
    with pytest.raises(OSError, match="interrupted write"):
        reopen_items(ws, [leaf.id])

    assert ws.load_item(story.id).status == "todo"
    assert ws.load_item(leaf.id).status == "done"

    monkeypatch.setattr(ws, "write_item", original_write_item)
    reopen_items(ws, [leaf.id])
    assert ws.load_item(story.id).status == "todo"
    assert ws.load_item(leaf.id).status == "todo"

    settled = {path: path.read_bytes() for path in ws.items_dir.iterdir()}
    reopen_items(ws, [leaf.id])
    assert {path: path.read_bytes() for path in ws.items_dir.iterdir()} == settled
