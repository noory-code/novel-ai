"""Tests for the HTTP API and Solera-root resolution."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from solera_mcp.server import create_http_app, resolve_solera_root, resolve_workspace


def _seed_workspace(workspace: Path) -> None:
    concepts = workspace / "concepts"
    concepts.mkdir(parents=True, exist_ok=True)
    (concepts / "auth.md").write_text(
        "---\nid: auth\nname: Auth\nstatus: active\n---\n\n"
        "# Intent\nUser proves identity.\n\n"
        "# Current Design\nPasswordless.\n\n"
        "# Current Shape\n(no Stories yet)\n",
        encoding="utf-8",
    )
    (workspace / "concept-graph.json").write_text(
        json.dumps({"edges": [{"from": "auth", "to": "auth", "label": "self"}]}),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# resolve_solera_root
# ---------------------------------------------------------------------------


def test_resolve_solera_root_prefers_dotsolera(tmp_path: Path) -> None:
    _seed_workspace(tmp_path / ".solera")
    resolved = resolve_solera_root(str(tmp_path))
    assert resolved == (tmp_path / ".solera").resolve()


def test_resolve_solera_root_accepts_dotsolera_dir_directly(tmp_path: Path) -> None:
    root = tmp_path / ".solera"
    _seed_workspace(root)
    resolved = resolve_solera_root(str(root))
    assert resolved == root.resolve()


def test_resolve_solera_root_falls_back_to_workspace_with_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Backward-compat: v3 `workspace/` layout still resolves but logs a warning.

    Drop this test when `solera-map` v0.2.0 removes the fallback.
    """
    _seed_workspace(tmp_path / "workspace")
    with caplog.at_level(logging.WARNING, logger="solera_mcp.server"):
        resolved = resolve_solera_root(str(tmp_path))
    assert resolved == (tmp_path / "workspace").resolve()
    assert any(
        "legacy v3 layout" in rec.message.lower()
        or "solera-migrate-workspace-to-dotsolera" in rec.message
        for rec in caplog.records
    ), f"expected v3 deprecation warning, got: {[r.message for r in caplog.records]}"


def test_resolve_solera_root_prefers_dotsolera_over_workspace(tmp_path: Path) -> None:
    """When both layouts exist (mid-migration), `.solera/` wins."""
    _seed_workspace(tmp_path / ".solera")
    _seed_workspace(tmp_path / "workspace")
    resolved = resolve_solera_root(str(tmp_path))
    assert resolved == (tmp_path / ".solera").resolve()


def test_resolve_solera_root_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        resolve_solera_root(str(tmp_path))


def test_resolve_workspace_alias_still_works(tmp_path: Path) -> None:
    """The `resolve_workspace` alias is kept for one minor version."""
    _seed_workspace(tmp_path / ".solera")
    assert resolve_workspace(str(tmp_path)) == resolve_solera_root(str(tmp_path))


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------


@pytest.fixture()
def client() -> TestClient:
    return TestClient(create_http_app())


def test_health_endpoint(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "solera-map"}


def test_graph_endpoint_requires_project_path(client: TestClient) -> None:
    r = client.get("/api/graph")
    assert r.status_code == 400
    assert "project_path" in r.json()["error"]


def test_graph_endpoint_returns_graph(client: TestClient, tmp_path: Path) -> None:
    _seed_workspace(tmp_path / ".solera")
    r = client.get("/api/graph", params={"project_path": str(tmp_path)})
    assert r.status_code == 200
    body = r.json()
    assert [c["id"] for c in body["concepts"]] == ["auth"]
    assert body["concept_edges"][0]["label"] == "self"
    assert body["milestones"] == []
    assert body["stories"] == []


def test_graph_endpoint_missing_workspace_returns_404(
    client: TestClient, tmp_path: Path
) -> None:
    r = client.get("/api/graph", params={"project_path": str(tmp_path)})
    assert r.status_code == 404
    assert "workspace" in r.json()["error"].lower()


# ---------------------------------------------------------------------------
# Layout endpoints
# ---------------------------------------------------------------------------


def test_layout_get_defaults_to_empty(client: TestClient, tmp_path: Path) -> None:
    _seed_workspace(tmp_path / ".solera")
    r = client.get("/api/layout", params={"project_path": str(tmp_path)})
    assert r.status_code == 200
    assert r.json() == {"nodes": {}}


def test_layout_put_and_get_roundtrip(client: TestClient, tmp_path: Path) -> None:
    _seed_workspace(tmp_path / ".solera")
    body = {
        "nodes": {
            "concept:auth": {"x": 120.5, "y": -40},
            "identity": {"x": 0, "y": 0, "collapsed": True},
        }
    }

    put_r = client.put(
        "/api/layout",
        params={"project_path": str(tmp_path)},
        json=body,
    )
    assert put_r.status_code == 200

    get_r = client.get("/api/layout", params={"project_path": str(tmp_path)})
    assert get_r.status_code == 200
    assert get_r.json() == body


def test_layout_put_requires_object_body(client: TestClient, tmp_path: Path) -> None:
    _seed_workspace(tmp_path / ".solera")
    r = client.put(
        "/api/layout",
        params={"project_path": str(tmp_path)},
        json=[1, 2, 3],
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# PATCH /api/concept/:id
# ---------------------------------------------------------------------------


def _write_concept(workspace: Path, concept_id: str, parent: str | None = None) -> None:
    concepts = workspace / "concepts"
    concepts.mkdir(parents=True, exist_ok=True)
    lines = ["---", f"id: {concept_id}", f"name: {concept_id.title()}", "status: active"]
    if parent is not None:
        lines.append(f"parent: {parent}")
    lines.append("---")
    lines.append("")
    lines.append(f"# Intent\nseed intent for {concept_id}.\n")
    (concepts / f"{concept_id}.md").write_text("\n".join(lines), encoding="utf-8")


def test_concept_patch_sets_parent(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / ".solera"
    _write_concept(ws, "app")
    _write_concept(ws, "profile")

    r = client.patch(
        "/api/concept/profile",
        params={"project_path": str(tmp_path)},
        json={"parent": "app"},
    )
    assert r.status_code == 200

    graph = client.get("/api/graph", params={"project_path": str(tmp_path)}).json()
    profile = next(c for c in graph["concepts"] if c["id"] == "profile")
    assert profile["parent"] == "app"


def test_concept_patch_clears_parent(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / ".solera"
    _write_concept(ws, "app")
    _write_concept(ws, "profile", parent="app")

    r = client.patch(
        "/api/concept/profile",
        params={"project_path": str(tmp_path)},
        json={"parent": None},
    )
    assert r.status_code == 200

    graph = client.get("/api/graph", params={"project_path": str(tmp_path)}).json()
    profile = next(c for c in graph["concepts"] if c["id"] == "profile")
    assert profile["parent"] is None


def test_concept_patch_rejects_unknown_parent(
    client: TestClient, tmp_path: Path
) -> None:
    _write_concept(tmp_path / ".solera", "profile")
    r = client.patch(
        "/api/concept/profile",
        params={"project_path": str(tmp_path)},
        json={"parent": "ghost"},
    )
    assert r.status_code == 400


def test_concept_patch_rejects_self_parent(client: TestClient, tmp_path: Path) -> None:
    _write_concept(tmp_path / ".solera", "profile")
    r = client.patch(
        "/api/concept/profile",
        params={"project_path": str(tmp_path)},
        json={"parent": "profile"},
    )
    assert r.status_code == 400


def test_concept_patch_rejects_cycle(client: TestClient, tmp_path: Path) -> None:
    ws = tmp_path / ".solera"
    _write_concept(ws, "a")
    _write_concept(ws, "b", parent="a")
    _write_concept(ws, "c", parent="b")
    # Making `a` a child of `c` would loop c → b → a → c.
    r = client.patch(
        "/api/concept/a",
        params={"project_path": str(tmp_path)},
        json={"parent": "c"},
    )
    assert r.status_code == 400


def test_concept_patch_rejects_disallowed_fields(
    client: TestClient, tmp_path: Path
) -> None:
    _write_concept(tmp_path / ".solera", "profile")
    r = client.patch(
        "/api/concept/profile",
        params={"project_path": str(tmp_path)},
        json={"name": "hacked"},
    )
    assert r.status_code == 400


def test_concept_patch_returns_404_for_missing_concept(
    client: TestClient, tmp_path: Path
) -> None:
    (tmp_path / ".solera" / "concepts").mkdir(parents=True)
    r = client.patch(
        "/api/concept/missing",
        params={"project_path": str(tmp_path)},
        json={"parent": None},
    )
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/concept/propose-from-narrative
# ---------------------------------------------------------------------------
#
# Critical Workflow-as-SSOT property the endpoint MUST preserve: a stub Concept
# is created with `# Intent` flagged "needs human review per
# solera-write-concept Moment 1 rule". The Concept is NOT finalized — humans
# must run `solera-write-concept update` to fill the Intent. These tests assert
# both the happy path and the guardrail.


def _write_narrative_for_propose(workspace: Path, narrative_id: str) -> None:
    narratives = workspace / "narratives"
    narratives.mkdir(parents=True, exist_ok=True)
    (narratives / f"{narrative_id}.md").write_text(
        "---\n"
        f"id: {narrative_id}\n"
        "kind: narrative\n"
        "form: user_story\n"
        "status: active\n"
        "created: 2026-04-01\n"
        'about: ["small-cafe-owner"]\n'
        "---\n\n"
        "# Statement\nAs a cafe owner, I want X so that Y.\n\n"
        "# Context\nMornings are chaotic.\n\n"
        "# Acceptance Cues\n- Order arrives within 1s.\n",
        encoding="utf-8",
    )


def test_propose_from_narrative_creates_stub_concept(
    client: TestClient, tmp_path: Path
) -> None:
    _seed_workspace(tmp_path / ".solera")  # an existing Concept dir + auth concept
    _write_narrative_for_propose(tmp_path / ".solera", "rush-orders-not-lost")

    r = client.post(
        "/api/concept/propose-from-narrative",
        params={"project_path": str(tmp_path)},
        json={
            "narrative_id": "rush-orders-not-lost",
            "concept_id": "order-tracking",
            "concept_name": "Order Tracking",
        },
    )

    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["concept_id"] == "order-tracking"
    assert body["needs_intent_review"] is True

    concept_path = tmp_path / ".solera" / "concepts" / "order-tracking.md"
    assert concept_path.exists()
    text = concept_path.read_text(encoding="utf-8")
    # The Moment 1 guardrail must be loud and unmistakable.
    assert "needs human review per solera-write-concept Moment 1 rule" in text
    assert "id: order-tracking" in text
    assert "name: Order Tracking" in text
    assert "status: active" in text
    # Provenance to the Narrative must round-trip.
    assert "[[narrative/rush-orders-not-lost]]" in text


def test_propose_from_narrative_appends_to_narrative_proposes(
    client: TestClient, tmp_path: Path
) -> None:
    _seed_workspace(tmp_path / ".solera")
    _write_narrative_for_propose(tmp_path / ".solera", "rush-orders-not-lost")

    r = client.post(
        "/api/concept/propose-from-narrative",
        params={"project_path": str(tmp_path)},
        json={
            "narrative_id": "rush-orders-not-lost",
            "concept_id": "order-tracking",
            "concept_name": "Order Tracking",
        },
    )
    assert r.status_code == 200

    narrative_text = (
        tmp_path / ".solera" / "narratives" / "rush-orders-not-lost.md"
    ).read_text(encoding="utf-8")
    assert "proposes:" in narrative_text
    assert "order-tracking" in narrative_text


def test_propose_from_narrative_rejects_existing_concept(
    client: TestClient, tmp_path: Path
) -> None:
    _seed_workspace(tmp_path / ".solera")  # creates concepts/auth.md
    _write_narrative_for_propose(tmp_path / ".solera", "rush-orders-not-lost")

    r = client.post(
        "/api/concept/propose-from-narrative",
        params={"project_path": str(tmp_path)},
        json={
            "narrative_id": "rush-orders-not-lost",
            "concept_id": "auth",  # already exists from _seed_workspace
            "concept_name": "Auth",
        },
    )
    assert r.status_code == 409
    assert "already exists" in r.json()["error"]


def test_propose_from_narrative_rejects_missing_narrative(
    client: TestClient, tmp_path: Path
) -> None:
    _seed_workspace(tmp_path / ".solera")

    r = client.post(
        "/api/concept/propose-from-narrative",
        params={"project_path": str(tmp_path)},
        json={
            "narrative_id": "no-such-narrative",
            "concept_id": "new-concept",
            "concept_name": "New",
        },
    )
    assert r.status_code == 404
    assert "not found" in r.json()["error"]


def test_propose_from_narrative_rejects_invalid_concept_id(
    client: TestClient, tmp_path: Path
) -> None:
    _seed_workspace(tmp_path / ".solera")
    _write_narrative_for_propose(tmp_path / ".solera", "rush-orders-not-lost")

    r = client.post(
        "/api/concept/propose-from-narrative",
        params={"project_path": str(tmp_path)},
        json={
            "narrative_id": "rush-orders-not-lost",
            "concept_id": "Bad ID With Spaces",
            "concept_name": "Bad",
        },
    )
    assert r.status_code == 400
    assert "kebab-case" in r.json()["error"]


def test_propose_from_narrative_requires_all_fields(
    client: TestClient, tmp_path: Path
) -> None:
    _seed_workspace(tmp_path / ".solera")
    _write_narrative_for_propose(tmp_path / ".solera", "n1")

    r = client.post(
        "/api/concept/propose-from-narrative",
        params={"project_path": str(tmp_path)},
        json={"narrative_id": "n1", "concept_id": "x"},  # missing concept_name
    )
    assert r.status_code == 400
    assert "concept_name" in r.json()["error"]
