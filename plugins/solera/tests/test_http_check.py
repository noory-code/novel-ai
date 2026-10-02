"""A person checks work items off over HTTP (D-2026-10-02-D).

An item with no gate and no children is finished by a person's check; a gated
leaf is finished only by its gate passing, which the check runs. The agent
surfaces (CLI, MCP) offer no way to finish an item without a gate.
"""

from __future__ import annotations

import asyncio
import shlex
import sys
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

import pytest
from starlette.testclient import TestClient

from solera import cli, mcp_server
from solera.broadcast import BroadcastHub
from solera.formats import Progress
from solera.http_app import create_http_app
from solera.planning import create_item
from solera.supervisor import check_item
from solera.workspace import Workspace


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False))) as test_client:
        yield test_client


def _query(root: Path) -> dict[str, str]:
    return {"project_path": str(root)}


def _ws(root: Path) -> Workspace:
    return Workspace(root / ".noory" / "solera")


def _py(code: str) -> str:
    return f"{shlex.quote(sys.executable)} -c {shlex.quote(code)}"


PASS = _py("import sys; sys.exit(0)")
FAIL = _py("import sys; print('three tests failed'); sys.exit(1)")


def _create(client: TestClient, root: Path, **body: Any) -> dict[str, Any]:
    body.setdefault("parent", None)
    body.setdefault("goal", "Goal")
    response = client.post("/api/work/items", params=_query(root), json=body)
    assert response.status_code == 201, response.text
    return cast(dict[str, Any], response.json())


def _check(client: TestClient, root: Path, item_id: str) -> Any:
    return client.post(f"/api/work/items/{item_id}/check", params=_query(root))


def _uncheck(client: TestClient, root: Path, item_id: str) -> Any:
    return client.delete(f"/api/work/items/{item_id}/check", params=_query(root))


def _status(root: Path, item_id: str) -> str:
    return _ws(root).load_item(item_id).status


def _mark_imported_design(root: Path) -> None:
    release = root / ".noory" / "solera" / "specs" / "auth"
    (release / "service").mkdir(parents=True)
    (release / "project").mkdir()
    (release / "service" / "manifest.json").write_text("{}")
    (release / "project" / "manifest.json").write_text("{}")


def test_checking_an_item_without_a_gate_finishes_it_and_rolls_up(
    client: TestClient, tmp_path: Path
) -> None:
    story = _create(client, tmp_path, goal="Pick a design")
    only = _create(client, tmp_path, parent=story["id"], goal="Choose the logo")

    response = _check(client, tmp_path, only["id"])

    assert response.status_code == 200, response.text
    assert response.json()["item"]["status"] == "done"
    assert response.json()["gate"] is None
    assert _status(tmp_path, story["id"]) == "done"
    progress = client.get("/api/work", params=_query(tmp_path)).json()["progress"]
    assert progress[story["id"]]["percent"] == 100


def test_checking_a_done_item_again_changes_nothing(client: TestClient, tmp_path: Path) -> None:
    item = _create(client, tmp_path)
    _check(client, tmp_path, item["id"])

    again = _check(client, tmp_path, item["id"])

    assert again.status_code == 200
    assert again.json() == {"item": _ws(tmp_path).load_item(item["id"]).model_dump(), "gate": None}


def test_a_container_cannot_be_checked(client: TestClient, tmp_path: Path) -> None:
    story = _create(client, tmp_path)
    _create(client, tmp_path, parent=story["id"])

    response = _check(client, tmp_path, story["id"])
    unchecked = _uncheck(client, tmp_path, story["id"])

    assert response.status_code == 400
    assert response.json()["code"] == "check_container"
    assert unchecked.status_code == 400
    assert unchecked.json()["code"] == "check_container"


def test_unknown_items_are_404(client: TestClient, tmp_path: Path) -> None:
    _create(client, tmp_path)

    assert _check(client, tmp_path, "ACT-999").json()["code"] == "unknown_work_item"
    assert _check(client, tmp_path, "ACT-999").status_code == 404
    assert _uncheck(client, tmp_path, "ACT-999").status_code == 404


def test_an_item_waiting_on_order_links_cannot_be_checked(
    client: TestClient, tmp_path: Path
) -> None:
    first = _create(client, tmp_path, goal="Sign the contract")
    second = _create(client, tmp_path, goal="Kick off", after=[first["id"]])

    response = _check(client, tmp_path, second["id"])

    assert response.status_code == 400
    assert response.json()["code"] == "check_blocked"
    assert first["id"] in response.json()["error"]
    assert _status(tmp_path, second["id"]) == "todo"


def test_an_item_that_reaches_no_design_node_cannot_be_checked(
    client: TestClient, tmp_path: Path
) -> None:
    _mark_imported_design(tmp_path)
    loose = _create(client, tmp_path, goal="Loose")
    linked = _create(client, tmp_path, goal="Linked", realizes=["feature/login"])

    assert _check(client, tmp_path, loose["id"]).json()["code"] == "check_blocked"
    assert _check(client, tmp_path, linked["id"]).status_code == 200


def test_waiting_items_without_a_gate_are_listed_as_blocked(
    client: TestClient, tmp_path: Path
) -> None:
    first = _create(client, tmp_path)
    second = _create(client, tmp_path, after=[first["id"]])

    view = client.get("/api/work", params=_query(tmp_path)).json()

    assert view["ready"] == []
    assert [entry["id"] for entry in view["blocked"]] == [second["id"]]
    assert view["blocked"][0]["waiting_on"] == [first["id"]]


def test_unchecking_reopens_the_item_and_its_rolled_up_parent(
    client: TestClient, tmp_path: Path
) -> None:
    story = _create(client, tmp_path)
    child = _create(client, tmp_path, parent=story["id"])
    _check(client, tmp_path, child["id"])

    response = _uncheck(client, tmp_path, child["id"])

    assert response.status_code == 200
    assert response.json()["item"]["status"] == "todo"
    assert _status(tmp_path, story["id"]) == "todo"
    assert _uncheck(client, tmp_path, child["id"]).json()["item"]["status"] == "todo"


def test_checking_a_gated_leaf_runs_its_gate(client: TestClient, tmp_path: Path) -> None:
    story = _create(client, tmp_path)
    leaf = _create(client, tmp_path, parent=story["id"], gate=PASS)

    response = _check(client, tmp_path, leaf["id"])

    assert response.status_code == 200
    body = response.json()
    assert body["item"]["status"] == "done"
    assert body["gate"]["passed"] is True
    assert body["gate"]["exit_code"] == 0
    assert _status(tmp_path, story["id"]) == "done"


def test_a_failing_gate_leaves_the_leaf_unchanged_and_reports_why(
    client: TestClient, tmp_path: Path
) -> None:
    leaf = _create(client, tmp_path, gate=FAIL)

    response = _check(client, tmp_path, leaf["id"])

    assert response.status_code == 200
    gate = response.json()["gate"]
    assert gate["passed"] is False
    assert gate["exit_code"] == 1
    assert gate["timed_out"] is False
    assert "three tests failed" in gate["output"]
    assert _status(tmp_path, leaf["id"]) == "todo"


def test_a_failing_gate_on_the_active_leaf_keeps_it_doing(
    client: TestClient, tmp_path: Path
) -> None:
    leaf = _create(client, tmp_path, gate=FAIL)
    ws = _ws(tmp_path)
    ws.write_item(ws.load_item(leaf["id"]).model_copy(update={"status": "doing"}))
    ws.write_progress(Progress(item=leaf["id"]))

    _check(client, tmp_path, leaf["id"])

    assert _status(tmp_path, leaf["id"]) == "doing"
    assert ws.load_progress().item == leaf["id"]


def test_passing_the_active_leaf_clears_the_pointer(client: TestClient, tmp_path: Path) -> None:
    leaf = _create(client, tmp_path, gate=PASS)
    ws = _ws(tmp_path)
    ws.write_item(ws.load_item(leaf["id"]).model_copy(update={"status": "doing"}))
    ws.write_progress(Progress(item=leaf["id"]))

    _check(client, tmp_path, leaf["id"])

    assert _status(tmp_path, leaf["id"]) == "done"
    assert ws.load_progress().item is None


def test_a_waiting_gated_leaf_is_not_run(client: TestClient, tmp_path: Path) -> None:
    first = _create(client, tmp_path, gate=PASS)
    second = _create(client, tmp_path, gate=PASS, after=[first["id"]])

    response = _check(client, tmp_path, second["id"])

    assert response.json()["code"] == "check_blocked"
    assert _status(tmp_path, second["id"]) == "todo"


def test_a_gate_verdict_cannot_be_undone_by_hand(client: TestClient, tmp_path: Path) -> None:
    leaf = _create(client, tmp_path, gate=PASS)
    _check(client, tmp_path, leaf["id"])

    response = _uncheck(client, tmp_path, leaf["id"])

    assert response.status_code == 400
    assert response.json()["code"] == "uncheck_gated"
    assert _status(tmp_path, leaf["id"]) == "done"


def test_the_gate_output_is_capped_to_its_tail(client: TestClient, tmp_path: Path) -> None:
    noisy = _py("import sys; print('x' * 9000 + 'END'); sys.exit(1)")
    leaf = _create(client, tmp_path, gate=noisy)

    output = _check(client, tmp_path, leaf["id"]).json()["gate"]["output"]

    assert len(output) == 4000
    assert output.rstrip().endswith("END")


def test_agent_surfaces_offer_no_way_to_finish_an_item_without_a_gate() -> None:
    parser = cli._build_parser()
    commands = next(action for action in parser._actions if action.dest == "command").choices
    tools = {tool.name for tool in asyncio.run(mcp_server.mcp.list_tools())}

    assert commands is not None
    assert not {"check", "uncheck"} & set(commands)
    assert not {name for name in tools if "check" in name}


def test_a_running_gate_does_not_hold_the_workspace_lock(tmp_path: Path) -> None:
    """A person's gate may run for minutes; the agent and the app must keep writing meanwhile."""
    ws = _ws(tmp_path)
    leaf = create_item(ws, "action", "slow", gate=_py("import time; time.sleep(1.0)"))
    outcome: dict[str, Any] = {}
    runner = threading.Thread(
        target=lambda: outcome.setdefault("result", check_item(ws, leaf.id, cwd=tmp_path))
    )

    runner.start()
    time.sleep(0.4)
    with ws.lock(timeout=0.2):
        pass
    runner.join()

    assert outcome["result"].item.status == "done"


def test_an_item_changed_while_its_gate_ran_is_not_marked_done(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    leaf = create_item(ws, "action", "slow", gate=_py("import time; time.sleep(0.8)"))
    errors: list[Exception] = []

    def run() -> None:
        try:
            check_item(ws, leaf.id, cwd=tmp_path)
        except Exception as exc:  # noqa: BLE001 - the test inspects the raised error
            errors.append(exc)

    runner = threading.Thread(target=run)
    runner.start()
    time.sleep(0.3)
    with ws.lock(timeout=1.0):
        ws.write_item(ws.load_item(leaf.id).model_copy(update={"gate": PASS}))
    runner.join()

    assert [getattr(error, "code", None) for error in errors] == ["check_conflict"]
    assert ws.load_item(leaf.id).status == "todo"
