"""Dev-only command channel — the drive half of the debug bridge.

``/api/debug`` lets an outside agent *read* the app's screen. This is the
opposite direction: the agent hands the running WKWebView a snippet to run and
gets the value back. CDP tools cannot attach to that webview on macOS and
``tauri-driver`` does not support macOS, so without this the app can only be
driven by a person's hands.

Same flavor gate as the snapshot half: registered only under
``MASHBILL_DEBUG=1``, which the shell sets only when the debug feature is
compiled in. A release build has no such route.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

from mashbill.broadcast import BroadcastHub
from mashbill.debug_endpoints import reset_debug_store
from mashbill.http_app import create_http_app


@pytest.fixture(autouse=True)
def _enable_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MASHBILL_DEBUG", "1")


@pytest.fixture(autouse=True)
def _clean_store() -> None:
    reset_debug_store()


def _app() -> Starlette:
    return create_http_app(hub=BroadcastHub(enable_watchers=False))


def _client() -> TestClient:
    return TestClient(_app())


def _async_client() -> httpx.AsyncClient:
    app = _app()
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://engine",
    )


def test_routes_absent_without_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Release flavor: no way in. This is the one that keeps `eval` out."""
    monkeypatch.delenv("MASHBILL_DEBUG", raising=False)
    client = _client()
    assert client.get("/api/debug/command").status_code in (404, 405)
    assert client.post("/api/debug/command", json={"script": "1"}).status_code in (404, 405)
    assert client.post("/api/debug/result", json={"id": 1}).status_code in (404, 405)


def test_nothing_to_run_when_no_one_asked() -> None:
    r = _client().get("/api/debug/command")
    assert r.status_code == 200
    assert r.json() == {}


def test_command_needs_a_script() -> None:
    r = _client().post("/api/debug/command", json={})
    assert r.status_code == 400


async def test_the_app_runs_it_and_the_value_comes_back() -> None:
    """The whole loop: ask → the app takes it → the app answers → the asker gets it."""
    async with _async_client() as client:

        async def app_side() -> None:
            for _ in range(100):
                taken = (await client.get("/api/debug/command")).json()
                if taken:
                    await client.post(
                        "/api/debug/result",
                        json={"id": taken["id"], "ok": True, "value": taken["script"] + " ran"},
                    )
                    return
                await asyncio.sleep(0.01)

        asker = client.post("/api/debug/command", json={"script": "document.title"})
        answer, _ = await asyncio.gather(asker, app_side())

    body = answer.json()
    assert body["ok"] is True
    assert body["value"] == "document.title ran"


async def test_a_thrown_error_comes_back_as_an_error() -> None:
    """A snippet that throws must not read as silence — silence means the app is gone."""
    async with _async_client() as client:

        async def app_side() -> None:
            for _ in range(100):
                taken = (await client.get("/api/debug/command")).json()
                if taken:
                    await client.post(
                        "/api/debug/result",
                        json={"id": taken["id"], "ok": False, "error": "x is not defined"},
                    )
                    return
                await asyncio.sleep(0.01)

        asker = client.post("/api/debug/command", json={"script": "x"})
        answer, _ = await asyncio.gather(asker, app_side())

    body = answer.json()
    assert body["ok"] is False
    assert body["error"] == "x is not defined"


async def test_silence_says_whether_the_app_was_ever_there() -> None:
    """Timeout alone cannot tell 'the app is not running' from 'the snippet hung'.

    The answer carries when the app last asked for work, so the two are told
    apart instead of both reading as a dead channel.
    """
    async with _async_client() as client:
        never = (
            await client.post("/api/debug/command", json={"script": "1", "timeout_ms": 60})
        ).json()
        assert never["error"] == "timeout"
        assert never["last_poll_at"] is None

        await client.get("/api/debug/command")  # the app checks in, takes nothing

        after = (
            await client.post("/api/debug/command", json={"script": "1", "timeout_ms": 60})
        ).json()
        assert after["error"] == "timeout"
        assert after["last_poll_at"] is not None


async def test_a_second_ask_is_refused_while_one_is_waiting() -> None:
    """Quietly dropping the first one would make a command vanish with no trace."""
    async with _async_client() as client:
        first = asyncio.create_task(
            client.post("/api/debug/command", json={"script": "1", "timeout_ms": 300})
        )
        await asyncio.sleep(0.05)
        second = await client.post("/api/debug/command", json={"script": "2"})
        assert second.status_code == 409
        await first


def test_an_answer_to_nothing_is_refused() -> None:
    r = _client().post("/api/debug/result", json={"id": 999, "ok": True, "value": 1})
    assert r.status_code == 404


async def test_the_answer_says_which_screen_gave_it() -> None:
    """Two open screens answer in turn, and an answer that does not name its
    screen reads as one screen changing its mind."""
    async with _async_client() as client:

        async def app_side() -> None:
            for _ in range(100):
                taken = (await client.get("/api/debug/command?page=b&title=Novel")).json()
                if taken:
                    await client.post(
                        "/api/debug/result",
                        json={"id": taken["id"], "ok": True, "value": 2, "page": "b"},
                    )
                    return
                await asyncio.sleep(0.01)

        asker = client.post("/api/debug/command", json={"script": "1"})
        answer, _ = await asyncio.gather(asker, app_side())

    assert answer.json()["from"] == "b"


async def test_a_command_can_name_the_screen_it_wants() -> None:
    """Without this, driving one screen means closing every other one first."""
    async with _async_client() as client:
        asking = asyncio.create_task(
            client.post("/api/debug/command", json={"script": "1", "page": "b", "timeout_ms": 2000})
        )
        await asyncio.sleep(0.05)

        wrong = (await client.get("/api/debug/command?page=a")).json()
        assert wrong == {}, "다른 화면이 남의 일감을 가져갔다"

        right = (await client.get("/api/debug/command?page=b")).json()
        assert right["script"] == "1"
        await client.post(
            "/api/debug/result", json={"id": right["id"], "ok": True, "value": 1, "page": "b"}
        )
        assert (await asking).json()["value"] == 1


async def test_who_is_open_is_listed() -> None:
    async with _async_client() as client:
        assert (await client.get("/api/debug/pages")).json() == {"pages": []}
        await client.get("/api/debug/command?page=a&title=Novel&url=http://x/")
        await client.get("/api/debug/command?page=b&title=Novel")
        listed = (await client.get("/api/debug/pages")).json()["pages"]
        assert {p["id"] for p in listed} == {"a", "b"}
        assert next(p for p in listed if p["id"] == "a")["url"] == "http://x/"
        assert all(p["last_poll_at"] for p in listed)


def test_the_snapshot_half_still_works() -> None:
    """The two halves share a store; adding one must not empty the other."""
    client = _client()
    client.post("/api/debug", json={"theme": "dark"})
    client.get("/api/debug/command")
    assert client.get("/api/debug").json()["latest"] == {"theme": "dark"}
