"""Re-pin (INT-f) maps service and shared format-F changes onto work items.

Proposals are deterministic and read-only; a human approves before
``reopen_items`` mutates any work state.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from solera.intake import ImportedRelease
from solera.planning import create_item
from solera.repin import propose_repin, reopen_items
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
