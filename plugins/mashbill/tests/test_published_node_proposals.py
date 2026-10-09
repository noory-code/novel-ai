"""Published service releases and read-only node candidates for blocked work."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import cast

import pytest
from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.chat_provider import ChatProviderSelection, write_selection
from mashbill.chat_providers.base import ChatProvider
from mashbill.chat_session import ChatSessionRegistry
from mashbill.http_app import create_http_app
from mashbill.project_io import create_project
from mashbill.workspace import resolve_plot_root


class FakeProvider:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls: list[tuple[str, str | None]] = []

    async def complete_once(self, prompt: str, *, model: str | None = None) -> str:
        self.calls.append((prompt, model))
        return self.reply


def client(provider: FakeProvider | None = None) -> TestClient:
    registry = ChatSessionRegistry(factory=lambda _root, _name: cast(ChatProvider, provider))
    return TestClient(
        create_http_app(hub=BroadcastHub(enable_watchers=False), chat_registry_instance=registry)
    )


def snapshot(root: Path) -> dict[str, bytes | None]:
    return {
        str(path.relative_to(root)): path.read_bytes() if path.is_file() else None
        for path in root.rglob("*")
    }


def add_release(
    published: Path,
    service: str,
    release: str,
    elements: list[tuple[str, str]],
    *,
    scope: str = "service",
) -> Path:
    folder = published / service / release
    (folder / "design" / "features").mkdir(parents=True)
    if scope == "service" and not any(slug == f"service/{service}" for slug, _ in elements):
        elements = [(f"service/{service}", f"{service} service"), *elements]
    manifest = {
        "format_f_version": 1,
        "scope": scope,
        "service": f"service/{service}",
        "release": release,
        "based_on": "vP2",
        "git_sha": "…",
        "elements": [
            {
                "id": slug,
                "label": label,
                "kind": slug.split("/", 1)[0],
                "hash": "…",
                **({"flow": True} if slug.startswith("feature/") else {}),
            }
            for slug, label in elements
        ],
        "refs": {
            "anchors": {"mission": "mission", "core_values": [], "identity": []},
            "actors": [],
            "entities": [],
        },
    }
    (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    for slug, label in elements:
        if slug == "mission":
            name = "foundation.md"
        elif slug.startswith("service/"):
            name = "service.md"
        else:
            name = f"features/{slug.split('/', 1)[1]}.md"
        (folder / "design" / name).write_text(
            f"---\nid: {slug}\n---\n# {label}\nUseful design detail for {slug}.\n",
            encoding="utf-8",
        )
    return folder


@pytest.fixture
def published_project(tmp_path: Path) -> tuple[Path, Path, Path]:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    plot_root = resolve_plot_root(str(workspace))
    create_project(plot_root, "alpha", "Alpha")
    published = plot_root / "published"
    add_release(published, "zeta", "vS1", [("service/zeta", "Old Zeta")])
    add_release(published, "zeta", "vS2", [("service/zeta", "Zeta service")])
    add_release(published, "alpha", "vS2", [("feature/order", "Order food")])
    add_release(published, "alpha", "vS10", [("feature/pay", "Pay bill")])
    add_release(published, "alpha", "vS11", [], scope="project")
    mismatched = add_release(published, "alpha", "vS12", [("feature/wrong", "Wrong")])
    manifest = json.loads((mismatched / "manifest.json").read_text(encoding="utf-8"))
    manifest["service"] = "service/other"
    (mismatched / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    add_release(published, "alpha", "vS0", [("feature/bad", "Bad")])
    (published / "alpha" / "vS99").mkdir()
    add_release(published, "_project", "vP1", [("mission", "Mission")], scope="project")
    return workspace, plot_root, published


def release_url(workspace: Path, project: str = "alpha") -> str:
    return f"/api/projects/{project}/published-releases?project_path={workspace}"


def test_manifest_for_other_service_is_skipped(tmp_path: Path) -> None:
    from mashbill.work_proposals import latest_service_releases

    folder = add_release(tmp_path / "published", "x", "vS3", [("feature/x", "책 빌리기")])
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["service"] = "service/other"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert latest_service_releases(tmp_path) == []


def nodes_url(workspace: Path, project: str = "alpha") -> str:
    return f"/api/projects/{project}/work-proposals/nodes?project_path={workspace}"


def test_releases_latest_valid_service_only_and_pure(
    published_project: tuple[Path, Path, Path],
) -> None:
    workspace, plot_root, published = published_project
    before = snapshot(plot_root)
    response = client().get(release_url(workspace))
    assert response.status_code == 200
    assert response.json() == {
        "releases": [
            {"service": "alpha", "release": "vS10", "source": str(published / "alpha" / "vS10")},
            {"service": "zeta", "release": "vS2", "source": str(published / "zeta" / "vS2")},
        ]
    }
    assert snapshot(plot_root) == before


def test_wrong_project_id_is_404(published_project: tuple[Path, Path, Path]) -> None:
    workspace, _, _ = published_project
    assert client().get(release_url(workspace, "wrong")).status_code == 404
    assert client().post(nodes_url(workspace, "wrong"), json={"goal": "Order"}).status_code == 404


def test_nodes_filter_unknown_limit_three_and_read_only(
    published_project: tuple[Path, Path, Path],
) -> None:
    workspace, plot_root, _ = published_project
    write_selection(plot_root, ChatProviderSelection(provider="claude-code", model="sonnet"))
    provider = FakeProvider(
        json.dumps(
            {
                "candidates": [
                    {"slug": "feature/order", "reason": "Old release"},
                    {"slug": "feature/pay", "reason": "Handles payment"},
                    {"slug": "service/zeta", "reason": "Supports the service"},
                    {"slug": "feature/pay", "reason": "Duplicate"},
                    {"slug": "unknown", "reason": "Unknown"},
                ]
            }
        )
    )
    before = snapshot(plot_root)
    response = client(provider).post(
        nodes_url(workspace),
        json={"goal": "결제하기", "conditions": ["영수증 보기"], "ancestors": ["주문하기"]},
    )
    assert response.status_code == 200
    assert response.json() == {
        "candidates": [
            {"slug": "feature/pay", "label": "Pay bill", "reason": "Handles payment"},
            {"slug": "service/zeta", "label": "Zeta service", "reason": "Supports the service"},
        ]
    }
    assert len(provider.calls) == 1
    prompt, model = provider.calls[0]
    assert model == "sonnet"
    assert all(
        text in prompt
        for text in ("결제하기", "영수증 보기", "주문하기", "feature/pay", "Pay bill")
    )
    assert "feature/order" not in prompt
    assert "Useful design detail" in prompt
    assert snapshot(plot_root) == before


def test_fenced_reply_and_three_candidate_limit(
    published_project: tuple[Path, Path, Path],
) -> None:
    workspace, plot_root, published = published_project
    add_release(published, "beta", "vS1", [("service/beta", "Beta")])
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    provider = FakeProvider(
        '```json\n{"candidates": ['
        '{"slug":"feature/pay","reason":"A"},'
        '{"slug":"service/zeta","reason":"B"},'
        '{"slug":"service/beta","reason":"C"},'
        '{"slug":"feature/pay","reason":"D"}]}\n```'
    )
    response = client(provider).post(nodes_url(workspace), json={"goal": "Do work"})
    assert response.status_code == 200
    assert len(response.json()["candidates"]) == 3
    assert len(provider.calls) == 1


@pytest.mark.parametrize("reply", ['{"candidates":[{"slug":"missing","reason":"x"}]}', "not json"])
def test_all_invalid_reply_is_502_and_pure(
    published_project: tuple[Path, Path, Path], reply: str
) -> None:
    workspace, plot_root, _ = published_project
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    before = snapshot(plot_root)
    response = client(FakeProvider(reply)).post(nodes_url(workspace), json={"goal": "Do work"})
    assert response.status_code == 502
    assert response.json()["code"] == "proposal_failed"
    assert snapshot(plot_root) == before


def test_no_provider_and_timeout_are_pure(
    published_project: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    from mashbill import work_proposals

    workspace, plot_root, _ = published_project
    before = snapshot(plot_root)
    response = client().post(nodes_url(workspace), json={"goal": "Do work"})
    assert response.status_code == 409
    assert response.json()["code"] == "no_chat_provider"
    assert snapshot(plot_root) == before
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    before = snapshot(plot_root)
    monkeypatch.setattr(work_proposals, "NODE_PROPOSAL_TIMEOUT_SECONDS", 0.001)

    class SlowProvider(FakeProvider):
        async def complete_once(self, prompt: str, *, model: str | None = None) -> str:
            self.calls.append((prompt, model))
            await asyncio.sleep(0.1)
            return self.reply

    provider = SlowProvider("{}")
    response = client(provider).post(nodes_url(workspace), json={"goal": "Do work"})
    assert response.status_code == 502
    assert response.json()["code"] == "proposal_failed"
    assert response.json()["reason"] == "timed out"
    assert len(provider.calls) == 1
    assert snapshot(plot_root) == before


@pytest.mark.parametrize(
    "body",
    [
        {"goal": " "},
        {"goal": 12},
        {"goal": "ok", "conditions": "wrong"},
        {"goal": "ok", "conditions": [2]},
        {"goal": "ok", "ancestors": [None]},
    ],
)
def test_invalid_node_request_is_400(
    published_project: tuple[Path, Path, Path], body: dict[str, object]
) -> None:
    workspace, plot_root, _ = published_project
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    provider = FakeProvider("{}")
    response = client(provider).post(nodes_url(workspace), json=body)
    assert response.status_code == 400
    assert provider.calls == []


def test_node_prompt_limits_published_entries() -> None:
    from mashbill.work_proposals import build_node_prompt

    nodes = {f"feature/{index}": (f"Node {index}", "Design line") for index in range(205)}
    prompt = build_node_prompt("Work", [], [], nodes)
    listed = json.loads(prompt.split("Published nodes:\n", 1)[1])
    assert len(listed) == 200
    assert listed[-1]["slug"] == "feature/199"


def test_heading_is_design_line_when_no_other_text(tmp_path: Path) -> None:
    from mashbill.work_proposals import published_service_nodes

    folder = add_release(tmp_path, "alpha", "vS1", [("service/alpha", "Alpha")])
    (folder / "design" / "service.md").write_text("# Alpha\n", encoding="utf-8")
    nodes = published_service_nodes(
        [("alpha", folder, {"elements": [{"id": "service/alpha", "label": "Alpha"}]})]
    )
    assert nodes["service/alpha"] == ("Alpha", "# Alpha")
