"""Confirmed tree planning through the HTTP contract."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest
from starlette.testclient import TestClient

from solera.formats import WorkItem, dump_workitem, parse_workitem
from solera.http_app import create_http_app
from solera.workspace import Workspace


def _ws(project: Path) -> Workspace:
    return Workspace(project / ".noory" / "solera")


def _post(client: TestClient, project: Path, body: dict[str, Any]) -> Any:
    return client.post("/api/work/plans", params={"project_path": str(project)}, json=body)


def _body(
    *items: dict[str, Any], parent: str | None = None, request_id: str = "request-1"
) -> dict[str, Any]:
    return {"request_id": request_id, "parent": parent, "items": list(items)}


def _node(key: str, **changes: Any) -> dict[str, Any]:
    return {"key": key, "goal": key, "accept": "person", **changes}


def test_plain_word_fields_round_trip_and_preserve_legacy_bytes() -> None:
    old = WorkItem(id="STORY-001", level="story", status="todo", goal="Old")
    original = dump_workitem(old)
    parsed = parse_workitem(original, item_id=old.id)
    for field in ("conditions", "pass_examples", "fail_examples", "risks", "basis"):
        assert getattr(parsed, field) == []
        assert field not in original
    assert dump_workitem(parsed) == original
    values = {
        field: ["  words  "]
        for field in ("conditions", "pass_examples", "fail_examples", "risks", "basis")
    }
    updated = WorkItem(**{**old.model_dump(), **values})
    round_trip = parse_workitem(dump_workitem(updated), item_id=old.id)
    assert all(getattr(round_trip, field) == ["words"] for field in values)
    for field in values:
        with pytest.raises(ValueError):
            WorkItem(**{**old.model_dump(), field: ["  "]})


def test_patch_plain_word_fields_and_rejections(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    ws.write_item(WorkItem(id="STORY-001", level="story", status="todo", goal="First"))
    query = {"project_path": str(tmp_path)}
    with TestClient(create_http_app()) as client:
        fields = {
            field: ["  value  "]
            for field in ("conditions", "pass_examples", "fail_examples", "risks")
        }
        response = client.patch("/api/work/items/STORY-001", params=query, json=fields)
        assert response.status_code == 200
        assert all(response.json()[field] == ["value"] for field in fields)
        assert response.json()["basis"] == []
        before = ws.item_path("STORY-001").read_bytes()
        for field in fields:
            response = client.patch("/api/work/items/STORY-001", params=query, json={field: [" "]})
            assert response.status_code == 400
            assert response.json()["code"] == "invalid_plan"
            assert ws.item_path("STORY-001").read_bytes() == before
        assert (
            client.patch("/api/work/items/STORY-001", params=query, json={"basis": []}).json()[
                "code"
            ]
            == "invalid_request"
        )
        for status, expected in (("review", "item_protected"), ("cancelled", "check_cancelled")):
            ws.write_item(ws.load_item("STORY-001").model_copy(update={"status": status}))
            response = client.patch(
                "/api/work/items/STORY-001", params=query, json={"risks": ["risk"]}
            )
            assert response.json()["code"] == expected


def test_plan_roots_children_order_links_and_idempotency(tmp_path: Path) -> None:
    with TestClient(create_http_app()) as client:
        existing = client.post(
            "/api/work/items",
            params={"project_path": str(tmp_path)},
            json={"parent": None, "goal": "Existing", "accept": "children"},
        ).json()["id"]
        predecessor = client.post(
            "/api/work/items",
            params={"project_path": str(tmp_path)},
            json={"parent": None, "goal": "Before", "accept": "person"},
        ).json()["id"]
        body = _body(
            _node(
                "one",
                accept="children",
                children=[_node("two", after_keys=["three"]), _node("three", after=[predecessor])],
            ),
            parent=existing,
        )
        response = _post(client, tmp_path, body)
        assert response.status_code == 201, response.text
        created = response.json()["created"]
        assert list(created) == ["one", "two", "three"]
        assert [item["id"] for item in response.json()["items"]] == list(created.values())
        ws = _ws(tmp_path)
        assert ws.load_item(existing).children == [created["one"]]
        assert ws.load_item(created["one"]).children == [created["two"], created["three"]]
        assert ws.load_item(created["two"]).after == [created["three"]]
        assert ws.load_item(created["three"]).after == [predecessor]
        records = json.loads((ws.root / "plans.json").read_text())
        canonical = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        assert records == {
            body["request_id"]: {
                "body": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
                "created": created,
            }
        }
        files = ws.list_items()
        assert _post(client, tmp_path, body).status_code == 200
        assert ws.list_items() == files
        changed = {**body, "items": [_node("different")]}
        conflict = _post(client, tmp_path, changed)
        assert conflict.status_code == 409
        assert conflict.json()["code"] == "request_id_conflict"
        assert ws.list_items() == files
        roots = _post(client, tmp_path, _body(_node("root"), request_id="roots"))
        assert roots.status_code == 201
        assert roots.json()["created"]["root"] in ws.list_items()


@pytest.mark.parametrize(
    ("items", "code"),
    [
        ([_node("a", gate="true")], "invalid_request"),
        ([_node("a", accept="children")], "invalid_plan"),
        ([_node(" ")], "invalid_plan"),
        ([_node("a"), _node("a")], "invalid_plan"),
        ([_node("a", after_keys=["missing"])], "invalid_plan"),
        ([_node("a", after_keys=["b"]), _node("b", after_keys=["a"])], "order_cycle"),
        ([_node("a", after=["missing"])], "unknown_predecessor"),
        ([_node("a", realizes=[" "])], "invalid_realizes_slug"),
        ([_node("a", basis=[" "])], "invalid_plan"),
        (
            [_node("a", accept="children", children=[_node("b", after_keys=["a"])])],
            "order_waits_on_ancestor",
        ),
        (
            [_node("a", accept="children", after_keys=["b"], children=[_node("b")])],
            "order_waits_on_descendant",
        ),
    ],
)
def test_plan_rejects_invalid_tree_without_writing(
    tmp_path: Path, items: list[dict[str, Any]], code: str
) -> None:
    with TestClient(create_http_app()) as client:
        response = _post(client, tmp_path, _body(*items))
    assert response.status_code == 400
    assert response.json()["code"] == code
    assert _ws(tmp_path).list_items() == []
    assert not (_ws(tmp_path).root / "plans.json").exists()


@pytest.mark.parametrize(
    ("status", "gate", "code"),
    [
        ("review", "", "item_protected"),
        ("cancelled", "", "check_cancelled"),
        ("todo", "true", "parent_is_leaf"),
    ],
)
def test_plan_rejects_uneditable_parent(tmp_path: Path, status: str, gate: str, code: str) -> None:
    ws = _ws(tmp_path)
    ws.write_item(
        WorkItem(
            id="STORY-001",
            level="story",
            status=status,
            goal="Parent",
            gate=gate,
            accept="gate" if gate else "person",
        )
    )
    before = ws.item_path("STORY-001").read_bytes()
    with TestClient(create_http_app()) as client:
        response = _post(client, tmp_path, _body(_node("child"), parent="STORY-001"))
    assert response.json()["code"] == code
    assert ws.list_items() == ["STORY-001"]
    assert ws.item_path("STORY-001").read_bytes() == before


def test_plan_rolls_back_when_record_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import solera.plan_batch as planning

    ws = _ws(tmp_path)
    ws.write_item(
        WorkItem(id="STORY-001", level="story", status="todo", goal="Parent", accept="children")
    )
    before = ws.item_path("STORY-001").read_bytes()
    original = getattr(planning, "_atomic_write_text")

    def fail_record(path: Path, text: str) -> None:
        if path.name == "plans.json":
            raise OSError("injected failure")
        original(path, text)

    monkeypatch.setattr(planning, "_atomic_write_text", fail_record)
    with TestClient(create_http_app(), raise_server_exceptions=False) as client:
        response = _post(client, tmp_path, _body(_node("child"), parent="STORY-001"))
    assert response.status_code == 500
    assert ws.list_items() == ["STORY-001"]
    assert ws.item_path("STORY-001").read_bytes() == before
    assert not (ws.root / "plans.json").exists()


def test_plan_rejects_cancelled_subtree_and_unknown_parent(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    ws.write_item(
        WorkItem(
            id="STORY-001",
            level="story",
            status="cancelled",
            goal="Stopped",
            children=["ACT-001"],
            accept="children",
        )
    )
    ws.write_item(WorkItem(id="ACT-001", level="action", status="todo", goal="Frozen"))
    with TestClient(create_http_app()) as client:
        for parent, code in (("ACT-001", "check_cancelled"), ("missing", "unknown_parent")):
            response = _post(client, tmp_path, _body(_node("new"), parent=parent))
            assert response.json()["code"] == code
    assert ws.list_items() == ["ACT-001", "STORY-001"]


def test_http_document_example_is_shared_shape(tmp_path: Path) -> None:
    doc = (Path(__file__).parents[1] / "docs" / "HTTP.md").read_text()
    section = doc.split("## Planning a tree", 1)[1]
    example = json.loads(re.search(r"```json\s*(.*?)\s*```", section, re.S).group(1))  # type: ignore[union-attr]
    with TestClient(create_http_app()) as client:
        response = _post(client, tmp_path, example)
    assert response.status_code == 201, response.text
    created = response.json()["created"]
    items = {item["id"]: item for item in response.json()["items"]}
    assert items[created["k1"]]["children"] == [created["k2"], created["k3"]]
    assert items[created["k3"]]["after"] == [created["k2"]]
    for key, field in (
        ("k1", "basis"),
        ("k1", "conditions"),
        ("k2", "pass_examples"),
        ("k3", "fail_examples"),
        ("k3", "risks"),
    ):
        assert items[created[key]][field]
