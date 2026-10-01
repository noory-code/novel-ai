from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from mashbill.folder_io import create_project, read_canvas, write_canvas
from mashbill.models import ActorNode
from mashbill.workspace import resolve_plot_root


class FakeProvider:
    def __init__(self, reply: str = "{}", *, error: Exception | None = None) -> None:
        self.reply = reply
        self.error = error
        self.calls: list[tuple[str, str | None]] = []

    async def complete_once(self, prompt: str, *, model: str | None = None) -> str:
        self.calls.append((prompt, model))
        if self.error is not None:
            raise self.error
        return self.reply


class SlowProvider(FakeProvider):
    async def complete_once(self, prompt: str, *, model: str | None = None) -> str:
        self.calls.append((prompt, model))
        await asyncio.sleep(1)
        return self.reply


@pytest.fixture
def plot_root(tmp_path: Path) -> Path:
    root = resolve_plot_root(str(tmp_path))
    create_project(root, "alpha", "Alpha")
    return root


def _actors(plot_root: Path, *nodes: ActorNode) -> None:
    canvas = read_canvas(plot_root, "alpha", "actors")
    write_canvas(plot_root, "alpha", canvas.model_copy(update={"nodes": list(nodes)}))


def test_parse_slug_reply_ignores_unknown_and_invalid_values() -> None:
    from mashbill.slug_suggest import parse_slug_reply

    raw = 'before {"n1":"checkout","n2":"Check Out","unknown":"fine"} after'

    assert parse_slug_reply(raw, ["n1", "n2"]) == {"n1": "checkout"}


def test_parse_slug_reply_reads_code_fence() -> None:
    from mashbill.slug_suggest import parse_slug_reply

    assert parse_slug_reply('```json\n{"n1":"checkout"}\n```', ["n1"]) == {"n1": "checkout"}


def test_build_slug_prompt_contains_node_context_and_json_instruction() -> None:
    from mashbill.slug_suggest import build_slug_prompt

    prompt = build_slug_prompt([ActorNode(id="operator", label="운영자", body="서비스를 운영한다")])

    assert "운영자" in prompt
    assert '"kind": "actor"' in prompt
    assert "서비스를 운영한다" in prompt
    assert "Return only one JSON object" in prompt


async def test_slug_proposals_dedupes_provider_reply(plot_root: Path) -> None:
    from mashbill.format_f_slugs import write_slug_store
    from mashbill.slug_suggest import slug_proposals

    write_slug_store(plot_root, "alpha", {"fixed": "actor/admin"})
    _actors(
        plot_root,
        ActorNode(id="fixed", label="관리자"),
        ActorNode(id="english", label="Customer"),
        ActorNode(id="n1", label="구매자"),
        ActorNode(id="n2", label="판매자"),
    )
    provider = FakeProvider('{"n1":"person","n2":"person"}')

    result = await slug_proposals(
        plot_root,
        "alpha",
        "project",
        None,
        suggest=True,
        provider=provider,
        model="model-a",
    )

    assert result["ai_status"] == "ok"
    assert result["needed"] == [
        {
            "node_id": "n1",
            "kind": "actor",
            "label": "구매자",
            "proposed": "person",
            "deduped": False,
        },
        {
            "node_id": "n2",
            "kind": "actor",
            "label": "판매자",
            "proposed": "person-2",
            "deduped": True,
        },
    ]
    assert result["taken"] == ["actor/admin", "actor/customer"]
    assert provider.calls[0][1] == "model-a"


async def test_slug_proposals_avoids_automatic_english_id(plot_root: Path) -> None:
    from mashbill.slug_suggest import slug_proposals

    _actors(
        plot_root,
        ActorNode(id="english", label="Operator"),
        ActorNode(id="korean", label="운영자"),
    )
    provider = FakeProvider('{"korean":"operator"}')

    result = await slug_proposals(
        plot_root,
        "alpha",
        "project",
        None,
        suggest=True,
        provider=provider,
        model=None,
    )

    assert result["needed"][0]["proposed"] == "operator-2"
    assert result["needed"][0]["deduped"] is True


@pytest.mark.parametrize(
    ("suggest", "provider", "status"),
    [
        (False, FakeProvider('{"n1":"operator"}'), "skipped"),
        (True, None, "no_provider"),
    ],
)
async def test_slug_proposals_skips_without_calling_provider(
    plot_root: Path,
    suggest: bool,
    provider: FakeProvider | None,
    status: str,
) -> None:
    from mashbill.slug_suggest import slug_proposals

    _actors(plot_root, ActorNode(id="n1", label="운영자"))

    result = await slug_proposals(
        plot_root,
        "alpha",
        "project",
        None,
        suggest=suggest,
        provider=provider,
        model=None,
    )

    assert result["ai_status"] == status
    assert result["needed"][0]["proposed"] is None
    if provider is not None:
        assert provider.calls == []


async def test_slug_proposals_skips_when_no_names_are_needed(plot_root: Path) -> None:
    from mashbill.slug_suggest import slug_proposals

    _actors(plot_root, ActorNode(id="n1", label="Operator"))
    provider = FakeProvider('{"n1":"operator"}')

    result = await slug_proposals(
        plot_root,
        "alpha",
        "project",
        None,
        suggest=True,
        provider=provider,
        model=None,
    )

    assert result == {"needed": [], "taken": ["actor/operator"], "ai_status": "skipped"}
    assert provider.calls == []


@pytest.mark.parametrize("provider", [FakeProvider(error=RuntimeError("boom")), SlowProvider()])
async def test_slug_proposals_failure_returns_nulls(
    plot_root: Path,
    provider: FakeProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import mashbill.slug_suggest as slug_suggest

    _actors(plot_root, ActorNode(id="n1", label="운영자"))
    monkeypatch.setattr(slug_suggest, "SLUG_SUGGEST_TIMEOUT_SECONDS", 0.001)

    result = await slug_suggest.slug_proposals(
        plot_root,
        "alpha",
        "project",
        None,
        suggest=True,
        provider=provider,
        model=None,
    )

    assert result["ai_status"] == "failed"
    assert result["needed"][0]["proposed"] is None
