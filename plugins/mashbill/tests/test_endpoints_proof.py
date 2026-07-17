"""Read-only Proof-by-value HTTP endpoint tests (D-2026-07-17-D)."""

from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.http_app import create_http_app


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / ".noory" / "novel").mkdir(parents=True)
    return root


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))


def _write_proof(workspace: Path, proof_id: str, content: str) -> None:
    proof_root = workspace / ".noory" / "proof"
    proof_root.mkdir(parents=True, exist_ok=True)
    (proof_root / f"{proof_id}.md").write_text(content, encoding="utf-8")


def test_get_proof_returns_frontmatter_and_markdown_body(
    client: TestClient, workspace: Path
) -> None:
    _write_proof(
        workspace,
        "PROOF-42",
        """---
title: Keep decisions close to concepts
status: accepted
supersedes: PROOF-7
---

# Context

The entity points to this decision.
""",
    )

    response = client.get("/api/proof/PROOF-42", params={"project_path": str(workspace)})

    assert response.status_code == 200
    assert response.json() == {
        "id": "PROOF-42",
        "title": "Keep decisions close to concepts",
        "status": "accepted",
        "body": "# Context\n\nThe entity points to this decision.",
    }


def test_get_proof_missing_file_is_404_without_creating_proof_dir(
    client: TestClient, workspace: Path
) -> None:
    proof_root = workspace / ".noory" / "proof"

    response = client.get("/api/proof/PROOF-404", params={"project_path": str(workspace)})

    assert response.status_code == 404
    assert not proof_root.exists()


@pytest.mark.parametrize(
    "content",
    [
        "title: Missing leading fence\nstatus: accepted\n",
        "---\ntitle: [unterminated\nstatus: accepted\n---\nBody\n",
        "---\n- title\n- status\n---\nBody\n",
    ],
    ids=["missing-leading-fence", "bad-yaml", "not-a-mapping"],
)
def test_get_proof_malformed_frontmatter_is_422(
    client: TestClient, workspace: Path, content: str
) -> None:
    _write_proof(workspace, "PROOF-42", content)

    response = client.get("/api/proof/PROOF-42", params={"project_path": str(workspace)})

    assert response.status_code == 422


def test_get_proof_rejects_bad_id_shape(client: TestClient, workspace: Path) -> None:
    response = client.get("/api/proof/proof-42", params={"project_path": str(workspace)})

    assert response.status_code == 422
