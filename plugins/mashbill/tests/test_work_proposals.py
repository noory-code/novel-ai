"""Read-only format-F work proposals over the project HTTP surface."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any, cast

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
    def __init__(self, reply: str = "", error: Exception | None = None) -> None:
        self.reply = reply
        self.error = error
        self.calls: list[tuple[str, str | None]] = []

    async def complete_once(self, prompt: str, *, model: str | None = None) -> str:
        self.calls.append((prompt, model))
        if self.error:
            raise self.error
        return self.reply


@pytest.fixture
def setup(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    plot_root = resolve_plot_root(str(workspace))
    create_project(plot_root, "alpha", "Alpha")
    published = plot_root / "published"
    for release, elements, files in (
        ("_project/vP1", ["mission"], {"foundation.md": "old mission"}),
        (
            "_project/vP3",
            ["mission", "actor/customer", "entity/order"],
            {
                "foundation.md": "new mission 한국어",
                "actors.md": "customer actor text",
                "entities/order.md": "order entity text",
            },
        ),
        (
            "order/vS1",
            ["service/order", "feature/order-food", "feature/retired"],
            {
                "service.md": "old service text",
                "features/order-food.md": "old feature text",
                "features/retired.md": "retired feature text",
            },
        ),
        (
            "order/vS2",
            ["service/order", "feature/order-food"],
            {"service.md": "new service text", "features/order-food.md": "new feature text"},
        ),
    ):
        folder = published / release
        design = folder / "design"
        design.mkdir(parents=True)
        scope = "project" if release.startswith("_project") else "service"
        manifest = {
            "scope": scope,
            "release": release.split("/")[-1],
            "elements": [{"id": slug, "kind": slug.split("/")[0]} for slug in elements],
        }
        (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        for name, content in files.items():
            path = design / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    return workspace, plot_root


def client(provider: FakeProvider | None = None) -> TestClient:
    registry = ChatSessionRegistry(factory=lambda _root, _name: cast(ChatProvider, provider))
    return TestClient(
        create_http_app(hub=BroadcastHub(enable_watchers=False), chat_registry_instance=registry)
    )


def url(workspace: Path, name: str) -> str:
    return f"/api/projects/alpha/work-proposals/{name}?project_path={workspace}"


def tree(root: Path) -> dict[str, bytes | None]:
    return {
        str(path.relative_to(root)): path.read_bytes() if path.is_file() else None
        for path in root.rglob("*")
    }


def test_item_uses_latest_containing_release_and_never_writes(
    setup: tuple[Path, Path],
) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code", model="sonnet"))
    provider = FakeProvider(
        json.dumps(
            {
                "key": "root",
                "goal": "주문하기",
                "accept": "person",
                "conditions": ["결과를 확인한다"],
                "pass_examples": [],
                "fail_examples": [],
                "risks": [],
                "realizes": ["wrong"],
                "basis": ["wrong@vS9"],
            }
        )
    )
    before = tree(plot_root)
    response = client(provider).post(
        url(workspace, "item"),
        json={
            "slugs": ["feature/retired", "feature/order-food", "mission"],
            "outcome": "맛있게 주문",
        },
    )
    assert response.status_code == 200
    proposal = response.json()["proposal"]
    assert proposal["realizes"] == ["feature/retired", "feature/order-food", "mission"]
    assert proposal["basis"] == [
        "feature/retired@vS1",
        "feature/order-food@vS2",
        "mission@vP3",
    ]
    assert len(provider.calls) == 1
    prompt, model = provider.calls[0]
    assert model == "sonnet"
    for text in (
        "retired feature text",
        "old service text",
        "new feature text",
        "new service text",
        "new mission 한국어",
        "맛있게 주문",
    ):
        assert text in prompt
    assert "never include a check command" in prompt.lower()
    assert tree(plot_root) == before


@pytest.mark.parametrize(
    "reply_prefix, reply_suffix",
    [
        ("```json\n", "\n```"),
        ("Here is the proposal:\n", ""),
    ],
)
def test_item_reads_json_object_in_provider_reply(
    setup: tuple[Path, Path], reply_prefix: str, reply_suffix: str
) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    node = {
        "key": "root",
        "goal": "주문하기",
        "accept": "person",
        "conditions": ["주문을 확인한다"],
    }
    provider = FakeProvider(reply_prefix + json.dumps(node) + reply_suffix)

    response = client(provider).post(
        url(workspace, "item"), json={"slugs": ["mission"], "outcome": "주문하기"}
    )

    assert response.status_code == 200
    assert response.json()["proposal"] == {
        **node,
        "realizes": ["mission"],
        "basis": ["mission@vP3"],
    }


def test_item_reply_without_json_object_is_proposal_failed(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))

    response = client(FakeProvider("There is no proposal yet.")).post(
        url(workspace, "item"), json={"slugs": ["mission"], "outcome": "주문하기"}
    )

    assert response.status_code == 502
    assert response.json()["code"] == "proposal_failed"
    assert response.json()["reason"] == "reply is not valid JSON"


@pytest.mark.parametrize("name", ["item", "basis"])
def test_unknown_slug_and_bad_input(setup: tuple[Path, Path], name: str) -> None:
    workspace, plot_root = setup
    before = tree(plot_root)
    c = client()
    body: dict[str, Any] = {"slugs": ["feature/unknown"]}
    if name == "item":
        body["outcome"] = "result"
    response = c.post(url(workspace, name), json=body)
    assert response.status_code == 404
    assert response.json()["code"] == "unknown_slug"
    assert "feature/unknown" in response.json()["error"]
    assert c.post(url(workspace, name), json={**body, "slugs": []}).status_code == 400
    assert (
        c.post(url(workspace, name), json={**body, "slugs": ["mission", "mission"]}).status_code
        == 400
    )
    assert tree(plot_root) == before


def test_basis_read_is_ordered_and_pure(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    before = tree(plot_root)
    response = client().post(
        url(workspace, "basis"), json={"slugs": ["mission", "feature/retired", "entity/order"]}
    )
    assert response.status_code == 200
    assert response.json() == {"basis": ["mission@vP3", "feature/retired@vS1", "entity/order@vP3"]}
    assert tree(plot_root) == before


def test_item_rejects_blank_outcome_without_writing(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    before = tree(plot_root)
    response = client().post(url(workspace, "item"), json={"slugs": ["mission"], "outcome": "  "})
    assert response.status_code == 400
    assert tree(plot_root) == before


@pytest.mark.parametrize(
    "reply",
    [
        "not json",
        '{"key":"k","goal":" ","accept":"person"}',
        '{"key":"k","goal":"ok","accept":"gate"}',
        '{"key":"k","goal":"ok","accept":"person","after_keys":["missing"]}',
        '{"key":"k","goal":"ok","accept":"person","gate":"pytest"}',
        '{"key":"k","goal":"ok","accept":"children","children":[{"key":"c","goal":"ok","accept":"person","gate":"pytest"}]}',
        '{"key":"k","goal":"ok","accept":"person","children":[]}',
        '{"key":"k","goal":"ok","accept":"children","children":[]}',
        '{"key":"k","goal":"ok","accept":"person","conditions":[" "]}',
        '{"key":"k","goal":"ok","accept":"children","children":[{"key":"k","goal":"other","accept":"person"}]}',
    ],
)
def test_bad_reply_is_502_and_read_only(setup: tuple[Path, Path], reply: str) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    before = tree(plot_root)
    response = client(FakeProvider(reply)).post(
        url(workspace, "item"), json={"slugs": ["mission"], "outcome": "result"}
    )
    assert response.status_code == 502
    assert response.json()["code"] == "proposal_failed"
    assert response.json()["reason"]
    assert tree(plot_root) == before


def test_no_provider_and_timeout(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    before = tree(plot_root)
    response = client().post(
        url(workspace, "item"), json={"slugs": ["mission"], "outcome": "result"}
    )
    assert response.status_code == 409
    assert response.json()["code"] == "no_chat_provider"
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    before = tree(plot_root)
    response = client(FakeProvider(error=TimeoutError("slow"))).post(
        url(workspace, "item"), json={"slugs": ["mission"], "outcome": "result"}
    )
    assert response.status_code == 502
    assert response.json()["code"] == "proposal_failed"
    assert tree(plot_root) == before


def test_wait_for_timeout_is_502(setup: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    from mashbill import work_proposals

    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    before = tree(plot_root)
    monkeypatch.setattr(work_proposals, "WORK_PROPOSAL_TIMEOUT_SECONDS", 0.001)

    class SlowProvider(FakeProvider):
        async def complete_once(self, prompt: str, *, model: str | None = None) -> str:
            self.calls.append((prompt, model))
            await asyncio.sleep(0.1)
            return self.reply

    provider = SlowProvider("{}")
    response = client(provider).post(
        url(workspace, "item"), json={"slugs": ["mission"], "outcome": "result"}
    )
    assert response.status_code == 502
    assert response.json()["code"] == "proposal_failed"
    assert response.json()["reason"] == "timed out"
    assert len(provider.calls) == 1
    assert tree(plot_root) == before


def test_http_plan_example_pins_validator() -> None:
    from mashbill.work_proposals import validate_plan_node

    path = Path(__file__).resolve().parents[2] / "solera" / "docs" / "HTTP.md"
    doc = path.read_text(encoding="utf-8")
    section = doc.split("## Planning a tree", 1)[1]
    example = json.loads(re.search(r"```json\s*(.*?)```", section, re.DOTALL).group(1))  # type: ignore[union-attr]
    for node in [example["items"][0], *example["items"][0]["children"]]:
        validate_plan_node(node, known_keys={"k1", "k2", "k3"})
        with pytest.raises(ValueError):
            validate_plan_node({**node, "gate": "pytest"}, known_keys={"k1", "k2", "k3"})


def test_work_proposal_routes_are_registered() -> None:
    app = create_http_app(hub=BroadcastHub(enable_watchers=False))
    paths = {
        (getattr(route, "path", None), tuple(sorted(route.methods)))
        for route in app.routes
        if hasattr(route, "methods")
    }
    for name in ("item", "basis"):
        assert (f"/api/projects/{{project_id}}/work-proposals/{name}", ("POST",)) in paths
