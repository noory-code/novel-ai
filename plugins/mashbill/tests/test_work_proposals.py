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


@pytest.mark.parametrize("name", ["item", "basis"])
def test_flat_project_rejects_wrong_id_before_provider(setup: tuple[Path, Path], name: str) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    provider = FakeProvider(
        '{"key":"root","goal":"result","accept":"person","covered":["mission"]}'
    )
    c = client(provider)
    body: dict[str, Any] = {"slugs": ["mission"]}
    if name == "item":
        body["outcome"] = "result"

    wrong_url = url(workspace, name).replace("/projects/alpha/", "/projects/wrong/")
    response = c.post(wrong_url, json=body)
    assert response.status_code == 404
    assert response.json() == {"error": "project not found: wrong"}
    assert provider.calls == []

    response = c.post(url(workspace, name), json=body)
    assert response.status_code == 200
    if name == "item":
        assert response.json()["proposal"]["basis"] == ["mission@vP3"]
        assert len(provider.calls) == 1
    else:
        assert response.json() == {"basis": ["mission@vP3"]}
        assert provider.calls == []


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
                "covered": ["feature/retired", "feature/order-food", "mission"],
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


def test_item_reports_chosen_features_it_cannot_cover(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    selected = [
        "feature/order-food",
        "feature/retired",
        "mission",
        "actor/customer",
        "entity/order",
    ]
    provider = FakeProvider(
        json.dumps(
            {
                "key": "root",
                "goal": "주문 흐름",
                "accept": "person",
                "covered": selected[:2],
                "uncovered": [
                    {"slug": slug, "reason": "이 결과의 범위 밖입니다"} for slug in selected[2:]
                ],
            }
        )
    )

    response = client(provider).post(
        url(workspace, "item"), json={"slugs": selected, "outcome": "주문 흐름"}
    )

    assert response.status_code == 200
    assert response.json()["proposal"]["realizes"] == selected[:2]
    assert response.json()["uncovered"] == [
        {"slug": slug, "reason": "이 결과의 범위 밖입니다"} for slug in selected[2:]
    ]
    assert "EVERY chosen feature" in provider.calls[0][0]
    assert "covered" in provider.calls[0][0]


def test_item_refuses_unknown_covered_slug(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    provider = FakeProvider(
        json.dumps(
            {"key": "root", "goal": "주문", "accept": "person", "covered": ["feature/unknown"]}
        )
    )
    response = client(provider).post(
        url(workspace, "item"), json={"slugs": ["feature/order-food"], "outcome": "주문"}
    )
    assert response.status_code == 502
    assert "feature/unknown" in response.json()["reason"]


def test_item_child_coverage_counts_only_when_parent_includes_it(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    node = {
        "key": "root",
        "goal": "주문",
        "accept": "children",
        "covered": ["feature/order-food", "mission"],
        "children": [
            {"key": "a", "goal": "주문", "accept": "person", "covered": ["feature/order-food"]},
            {"key": "b", "goal": "미션", "accept": "person", "covered": ["mission"]},
        ],
    }
    c = client(FakeProvider(json.dumps(node)))
    body = {"slugs": ["feature/order-food", "mission"], "outcome": "주문"}
    response = c.post(url(workspace, "item"), json=body)
    assert response.status_code == 200
    assert response.json()["proposal"]["realizes"] == body["slugs"]
    assert [child["realizes"] for child in response.json()["proposal"]["children"]] == [
        ["feature/order-food"],
        ["mission"],
    ]
    assert "uncovered" not in response.json()

    node["covered"] = ["feature/order-food"]
    response = client(FakeProvider(json.dumps(node))).post(url(workspace, "item"), json=body)
    assert response.status_code == 502
    assert "parent" in response.json()["reason"]


def test_item_refuses_gap_without_reason(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    provider = FakeProvider(
        json.dumps(
            {"key": "root", "goal": "주문", "accept": "person", "covered": ["feature/order-food"]}
        )
    )
    response = client(provider).post(
        url(workspace, "item"),
        json={"slugs": ["feature/order-food", "mission"], "outcome": "주문"},
    )
    assert response.status_code == 502
    assert "uncovered" in response.json()["reason"]


def test_split_children_cover_only_their_features_and_report_gap(
    setup: tuple[Path, Path],
) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    body = split_body()
    body["item"]["realizes"] = ["feature/order-food", "mission", "entity/order"]
    provider = FakeProvider(
        json.dumps(
            {
                "items": [
                    {
                        "key": "a",
                        "goal": "주문",
                        "accept": "person",
                        "covered": ["feature/order-food"],
                    },
                    {"key": "b", "goal": "미션", "accept": "person", "covered": ["mission"]},
                ],
                "uncovered": [{"slug": "entity/order", "reason": "자료 결과가 없습니다"}],
            }
        )
    )
    response = client(provider).post(url(workspace, "split"), json=body)
    assert response.status_code == 200
    assert [item["realizes"] for item in response.json()["proposal"]["items"]] == [
        ["feature/order-food"],
        ["mission"],
    ]
    assert response.json()["uncovered"] == [
        {"slug": "entity/order", "reason": "자료 결과가 없습니다"}
    ]
    assert "union" in provider.calls[0][0]


def test_split_refuses_unknown_child_slug(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    provider = FakeProvider(
        json.dumps(
            {"items": [{"key": "a", "goal": "주문", "accept": "person", "covered": ["mission"]}]}
        )
    )
    response = client(provider).post(url(workspace, "split"), json=split_body())
    assert response.status_code == 502
    assert "mission" in response.json()["reason"]


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
        "covered": ["mission"],
    }
    provider = FakeProvider(reply_prefix + json.dumps(node) + reply_suffix)

    response = client(provider).post(
        url(workspace, "item"), json={"slugs": ["mission"], "outcome": "주문하기"}
    )

    assert response.status_code == 200
    assert response.json()["proposal"] == {
        **{key: value for key, value in node.items() if key != "covered"},
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


def stamp_versions(plot_root: Path) -> None:
    """Give the fixture releases blueprint versions and vP links, plus a second service's vS1."""
    published = plot_root / "published"
    for release, extra in (
        ("_project/vP1", {"blueprint_version": "v0.1.0"}),
        ("_project/vP3", {"blueprint_version": "v0.2.0"}),
        ("order/vS1", {"based_on": "vP1"}),
        ("order/vS2", {"based_on": "vP3"}),
    ):
        path = published / release / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(json.dumps({**manifest, **extra}), encoding="utf-8")
    pay = published / "pay" / "vS1"
    pay.mkdir(parents=True)
    (pay / "manifest.json").write_text(
        json.dumps(
            {
                "scope": "service",
                "release": "vS1",
                "based_on": "vP3",
                "elements": [{"id": "service/pay"}, {"id": "feature/pay"}],
            }
        ),
        encoding="utf-8",
    )


def test_versions_map_each_pin_to_its_blueprint_version(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    stamp_versions(plot_root)
    before = tree(plot_root)
    pins = [
        "mission@vP3",
        "mission@vP1",
        "feature/retired@vS1",
        "feature/order-food@vS2",
        "feature/pay@vS1",
        "feature/unknown@vS1",
        "entity/order@vP1",
        "feature/order-food@vS9",
        "no-release",
    ]
    response = client().post(url(workspace, "versions"), json={"pins": pins})
    assert response.status_code == 200
    assert response.json() == {
        "versions": {
            "mission@vP3": "v0.2.0",
            "mission@vP1": "v0.1.0",
            "feature/retired@vS1": "v0.1.0",
            "feature/order-food@vS2": "v0.2.0",
            "feature/pay@vS1": "v0.2.0",
            "feature/unknown@vS1": None,
            "entity/order@vP1": None,
            "feature/order-food@vS9": None,
            "no-release": None,
        }
    }
    assert tree(plot_root) == before


def test_versions_are_null_without_blueprint_version_or_vp_link(
    setup: tuple[Path, Path],
) -> None:
    workspace, _ = setup
    response = client().post(
        url(workspace, "versions"), json={"pins": ["mission@vP3", "feature/order-food@vS2"]}
    )
    assert response.status_code == 200
    assert response.json() == {"versions": {"mission@vP3": None, "feature/order-food@vS2": None}}


def test_versions_rejects_bad_input_and_wrong_project(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    before = tree(plot_root)
    c = client()
    bad: list[Any] = [{}, {"pins": "mission@vP3"}, {"pins": [1]}, []]
    for body in bad:
        assert c.post(url(workspace, "versions"), json=body).status_code == 400
    assert c.post(url(workspace, "versions"), json={"pins": []}).json() == {"versions": {}}
    wrong = url(workspace, "versions").replace("/projects/alpha/", "/projects/wrong/")
    assert c.post(wrong, json={"pins": ["mission@vP3"]}).status_code == 404
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
    for name in ("item", "basis", "split", "versions"):
        assert (f"/api/projects/{{project_id}}/work-proposals/{name}", ("POST",)) in paths


def split_body() -> dict[str, Any]:
    return {
        "item": {
            "goal": "주문자가 음식을 주문한다",
            "conditions": ["메뉴를 고르고 주문을 확정할 수 있다"],
            "pass_examples": ["메뉴 열 개 중 하나를 주문한다"],
            "fail_examples": ["품절 메뉴를 주문하려고 한다"],
            "risks": ["같은 주문이 두 번 들어간다"],
            "realizes": ["feature/order-food", "feature/unknown"],
            "basis": ["feature/order-food@vS1"],
        },
        "existing_children": ["이미 보이는 결과"],
    }


def split_reply() -> dict[str, Any]:
    return {
        "items": [
            {
                "key": "k2",
                "goal": "메뉴 목록을 보인다",
                "accept": "person",
                "covered": ["feature/order-food"],
            },
            {
                "key": "k3",
                "goal": "주문을 확정한다",
                "accept": "person",
                "after_keys": ["k2"],
                "covered": ["feature/unknown"],
                "realizes": ["wrong"],
                "basis": ["wrong@vS9"],
            },
        ]
    }


def test_split_uses_design_and_is_read_only(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code", model="sonnet"))
    before = tree(plot_root)
    provider = FakeProvider(json.dumps(split_reply()))

    response = client(provider).post(url(workspace, "split"), json=split_body())

    assert response.status_code == 200
    assert response.json() == {
        "proposal": {
            "items": [
                {
                    "key": "k2",
                    "goal": "메뉴 목록을 보인다",
                    "accept": "person",
                    "realizes": ["feature/order-food"],
                },
                {
                    "key": "k3",
                    "goal": "주문을 확정한다",
                    "accept": "person",
                    "after_keys": ["k2"],
                    "realizes": ["feature/unknown"],
                },
            ]
        }
    }
    assert len(provider.calls) == 1
    prompt, model = provider.calls[0]
    assert model == "sonnet"
    for value in (
        "주문자가 음식을 주문한다",
        "이미 보이는 결과",
        "new feature text",
        "new service text",
        "after_keys",
    ):
        assert value in prompt
    assert "old feature text" not in prompt
    assert tree(plot_root) == before


def test_split_works_without_published_realizes_and_reads_fence(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    before = tree(plot_root)
    reply = split_reply()
    reply["items"][0]["covered"] = []
    provider = FakeProvider("```json\n" + json.dumps(reply) + "\n```")
    body = split_body()
    body["item"]["realizes"] = ["feature/unknown"]

    response = client(provider).post(url(workspace, "split"), json=body)

    assert response.status_code == 200
    assert "new feature text" not in provider.calls[0][0]
    assert tree(plot_root) == before


@pytest.mark.parametrize(
    "reply",
    [
        {"items": []},
        {"items": [{"key": "k2", "goal": "first", "accept": "person", "gate": "pytest"}]},
        {
            "items": [
                {"key": "k2", "goal": "first", "accept": "person"},
                {"key": "k2", "goal": "second", "accept": "person"},
            ]
        },
        {
            "items": [
                {
                    "key": "parent",
                    "goal": "whole",
                    "accept": "children",
                    "children": [
                        {"key": "k2", "goal": "part", "accept": "person", "gate": "pytest"}
                    ],
                }
            ]
        },
        {
            "items": [
                {
                    "key": "parent",
                    "goal": "whole",
                    "accept": "children",
                    "children": [{"key": "k2", "goal": "part", "accept": "person"}],
                },
                {"key": "k2", "goal": "other", "accept": "person"},
            ]
        },
        {"items": [{"key": "k2", "goal": "first", "accept": "person", "after_keys": ["missing"]}]},
        {"items": [{"key": "k2", "goal": " 이미 보이는 결과 ", "accept": "person"}]},
    ],
)
def test_split_bad_reply_is_502_and_read_only(
    setup: tuple[Path, Path], reply: dict[str, Any]
) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    before = tree(plot_root)
    provider = FakeProvider(json.dumps(reply))

    response = client(provider).post(url(workspace, "split"), json=split_body())

    assert response.status_code == 502
    assert response.json()["code"] == "proposal_failed"
    assert response.json()["reason"]
    assert len(provider.calls) == 1
    assert tree(plot_root) == before


def test_split_no_provider(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    before = tree(plot_root)
    response = client().post(url(workspace, "split"), json=split_body())
    assert response.status_code == 409
    assert response.json()["code"] == "no_chat_provider"
    assert tree(plot_root) == before


def test_split_wait_for_timeout_is_502(
    setup: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    from mashbill import work_proposals

    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    before = tree(plot_root)
    monkeypatch.setattr(work_proposals, "SPLIT_PROPOSAL_TIMEOUT_SECONDS", 0.001)

    class SlowProvider(FakeProvider):
        async def complete_once(self, prompt: str, *, model: str | None = None) -> str:
            self.calls.append((prompt, model))
            await asyncio.sleep(0.1)
            return self.reply

    provider = SlowProvider(json.dumps(split_reply()))
    response = client(provider).post(url(workspace, "split"), json=split_body())
    assert response.status_code == 502
    assert response.json()["reason"] == "timed out"
    assert len(provider.calls) == 1
    assert tree(plot_root) == before


def test_split_provider_timeout_and_wrong_project(setup: tuple[Path, Path]) -> None:
    workspace, plot_root = setup
    write_selection(plot_root, ChatProviderSelection(provider="claude-code"))
    before = tree(plot_root)
    provider = FakeProvider(error=TimeoutError("slow"))
    c = client(provider)
    response = c.post(url(workspace, "split"), json=split_body())
    assert response.status_code == 502
    assert response.json()["reason"] == "timed out"
    wrong_url = url(workspace, "split").replace("/projects/alpha/", "/projects/wrong/")
    response = c.post(wrong_url, json=split_body())
    assert response.status_code == 404
    assert response.json() == {"error": "project not found: wrong"}
    assert len(provider.calls) == 1
    assert tree(plot_root) == before


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"item": {"goal": " "}},
        {"item": {"goal": "ok", "conditions": [" "]}},
        {"item": {"goal": "ok", "basis": "bad"}},
        {"item": {"goal": "ok"}, "existing_children": [1]},
    ],
)
def test_split_bad_request_is_400(setup: tuple[Path, Path], body: dict[str, Any]) -> None:
    workspace, plot_root = setup
    before = tree(plot_root)
    response = client().post(url(workspace, "split"), json=body)
    assert response.status_code == 400
    assert tree(plot_root) == before


def test_http_plan_example_children_pin_split_validator() -> None:
    from mashbill.work_proposals import validate_split_proposal

    path = Path(__file__).resolve().parents[2] / "solera" / "docs" / "HTTP.md"
    doc = path.read_text(encoding="utf-8")
    section = doc.split("## Planning a tree", 1)[1]
    example = json.loads(re.search(r"```json\s*(.*?)```", section, re.DOTALL).group(1))  # type: ignore[union-attr]
    children = example["items"][0]["children"]
    assert validate_split_proposal({"items": children}, []) == {"items": children}
    with pytest.raises(ValueError):
        validate_split_proposal({"items": [{**children[0], "gate": "pytest"}, children[1]]}, [])
    with pytest.raises(ValueError):
        validate_split_proposal({"items": children}, [" 메뉴 목록을 보인다 "])
