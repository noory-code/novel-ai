"""HTTP-level tests for the v5.1 CRUD endpoints across all five kinds.

Uses Starlette's TestClient against :func:`create_http_app` with a seeded
`.solera/` tree on disk per test. Covers happy paths, allowed-key
enforcement, and the main cross-ref rejections.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from solera_mcp.broadcast import BroadcastHub
from solera_mcp.http_app import create_http_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))


def _seed(tmp_path: Path) -> None:
    """Create a minimal `.solera/` with one Role so Personas / Journeys can reference it."""
    solera = tmp_path / ".solera"
    (solera / "identity").mkdir(parents=True)
    (solera / "identity" / "mission.md").write_text(
        "---\nid: mission\nkind: identity\n---\n\n# Mission\nTest.\n",
        encoding="utf-8",
    )
    (solera / "roles").mkdir()
    (solera / "roles" / "customer.md").write_text(
        "---\nid: customer\nkind: role\nname: Customer\nstatus: active\n"
        "created: 2026-04-19\n---\n\n# Description\nA buyer.\n",
        encoding="utf-8",
    )
    (solera / "personas").mkdir()
    (solera / "journeys").mkdir()
    (solera / "narratives").mkdir()
    (solera / "concepts").mkdir()


# ---------------------------------------------------------------------------
# Role POST + PATCH
# ---------------------------------------------------------------------------


def test_role_post_creates_file(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    r = client.post(
        "/api/role",
        params={"project_path": str(tmp_path)},
        json={"id": "admin", "name": "Admin", "description": "Operator."},
    )
    assert r.status_code == 200, r.text
    assert r.json()["ok"] is True
    path = tmp_path / ".solera" / "roles" / "admin.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "# Description" in text
    assert "Operator." in text


def test_role_post_rejects_duplicate(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    r = client.post(
        "/api/role",
        params={"project_path": str(tmp_path)},
        json={"id": "customer", "description": "Duplicate."},
    )
    assert r.status_code == 409


def test_role_post_rejects_invalid_kebab(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    r = client.post(
        "/api/role",
        params={"project_path": str(tmp_path)},
        json={"id": "Bad Id", "description": "x"},
    )
    assert r.status_code == 400


def test_role_patch_updates_description(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    r = client.patch(
        "/api/role/customer",
        params={"project_path": str(tmp_path)},
        json={"description": "An updated buyer description."},
    )
    assert r.status_code == 200, r.text
    text = (tmp_path / ".solera" / "roles" / "customer.md").read_text("utf-8")
    assert "An updated buyer description." in text


def test_role_patch_rejects_self_parent(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    r = client.patch(
        "/api/role/customer",
        params={"project_path": str(tmp_path)},
        json={"parent": "customer"},
    )
    assert r.status_code == 400


def test_role_patch_rejects_unknown_field(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    r = client.patch(
        "/api/role/customer",
        params={"project_path": str(tmp_path)},
        json={"secret_field": "x"},
    )
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Persona POST + PATCH — Role validation
# ---------------------------------------------------------------------------


def test_persona_post_requires_existing_role(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    r = client.post(
        "/api/persona",
        params={"project_path": str(tmp_path)},
        json={
            "id": "alice",
            "role": "does-not-exist",
            "identity": "Alice.",
        },
    )
    assert r.status_code == 400
    assert "Role" in r.json()["error"]


def test_persona_post_writes_identity_and_goals(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    r = client.post(
        "/api/persona",
        params={"project_path": str(tmp_path)},
        json={
            "id": "alice",
            "role": "customer",
            "identity": "Alice is a buyer.",
            "goals": ["Buy fast", "Stay loyal"],
        },
    )
    assert r.status_code == 200
    text = (tmp_path / ".solera" / "personas" / "alice.md").read_text("utf-8")
    assert "role: customer" in text
    assert "Alice is a buyer." in text
    assert "Buy fast" in text


def test_persona_patch_can_change_role(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    (tmp_path / ".solera" / "roles" / "admin.md").write_text(
        "---\nid: admin\nkind: role\nname: Admin\nstatus: active\n"
        "created: 2026-04-19\n---\n\n# Description\nOp.\n",
        encoding="utf-8",
    )
    client.post(
        "/api/persona",
        params={"project_path": str(tmp_path)},
        json={"id": "alice", "role": "customer", "identity": "."},
    )
    r = client.patch(
        "/api/persona/alice",
        params={"project_path": str(tmp_path)},
        json={"role": "admin"},
    )
    assert r.status_code == 200
    text = (tmp_path / ".solera" / "personas" / "alice.md").read_text("utf-8")
    assert "role: admin" in text


# ---------------------------------------------------------------------------
# Journey POST + PATCH
# ---------------------------------------------------------------------------


def test_journey_post_requires_walks_role_to_exist(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    r = client.post(
        "/api/journey",
        params={"project_path": str(tmp_path)},
        json={
            "id": "first-purchase",
            "walks": "ghost-role",
            "trigger": "T",
            "outcome": "O",
            "steps": [],
        },
    )
    assert r.status_code == 400


def test_journey_patch_updates_steps(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    client.post(
        "/api/journey",
        params={"project_path": str(tmp_path)},
        json={
            "id": "first-purchase",
            "walks": "customer",
            "trigger": "They want to buy.",
            "outcome": "They did.",
            "steps": [],
        },
    )
    r = client.patch(
        "/api/journey/first-purchase",
        params={"project_path": str(tmp_path)},
        json={
            "steps": [
                {
                    "n": 1,
                    "stage": "Browse",
                    "step": "Open app",
                    "touchpoint": "Mobile",
                    "emotion": "😀",
                    "pain": "—",
                },
            ]
        },
    )
    assert r.status_code == 200, r.text
    text = (tmp_path / ".solera" / "journeys" / "first-purchase.md").read_text("utf-8")
    assert "Open app" in text


# ---------------------------------------------------------------------------
# Narrative POST + PATCH
# ---------------------------------------------------------------------------


def test_narrative_post_requires_about_roles(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    r = client.post(
        "/api/narrative",
        params={"project_path": str(tmp_path)},
        json={
            "id": "loose",
            "about_roles": [],
            "statement": "S",
            "context": "C",
            "acceptance_cues": ["c"],
        },
    )
    assert r.status_code == 400


def test_narrative_post_validates_about_role_ref(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    r = client.post(
        "/api/narrative",
        params={"project_path": str(tmp_path)},
        json={
            "id": "loose",
            "about_roles": ["ghost"],
            "statement": "S",
            "context": "C",
            "acceptance_cues": ["c"],
        },
    )
    assert r.status_code == 400


def test_narrative_patch_updates_context(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    create_resp = client.post(
        "/api/narrative",
        params={"project_path": str(tmp_path)},
        json={
            "id": "loose-narrative",
            "about_roles": ["customer"],
            "statement": "S",
            "context": "original",
            "acceptance_cues": ["c"],
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    r = client.patch(
        "/api/narrative/loose-narrative",
        params={"project_path": str(tmp_path)},
        json={"context": "new context"},
    )
    assert r.status_code == 200
    text = (tmp_path / ".solera" / "narratives" / "loose-narrative.md").read_text("utf-8")
    assert "new context" in text
    assert "# Statement" in text  # other sections still intact


# ---------------------------------------------------------------------------
# Concept POST + PATCH
# ---------------------------------------------------------------------------


def test_concept_post_creates_stub_with_intent(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    r = client.post(
        "/api/concept",
        params={"project_path": str(tmp_path)},
        json={
            "id": "auth",
            "name": "Auth",
            "intent": "User proves identity.",
            "current_design": "Passwordless.",
            "current_shape": "(no Stories)",
        },
    )
    assert r.status_code == 200
    text = (tmp_path / ".solera" / "concepts" / "auth.md").read_text("utf-8")
    assert "User proves identity." in text


def test_concept_patch_can_update_intent(client: TestClient, tmp_path: Path) -> None:
    _seed(tmp_path)
    (tmp_path / ".solera" / "concepts" / "auth.md").write_text(
        "---\nid: auth\nname: Auth\nstatus: active\n---\n\n"
        "# Intent\nOld intent.\n\n# Current Design\nX.\n\n# Current Shape\nY.\n",
        encoding="utf-8",
    )
    r = client.patch(
        "/api/concept/auth",
        params={"project_path": str(tmp_path)},
        json={"intent": "Updated intent."},
    )
    assert r.status_code == 200
    text = (tmp_path / ".solera" / "concepts" / "auth.md").read_text("utf-8")
    assert "Updated intent." in text
    # Other sections stay.
    assert "# Current Design" in text
