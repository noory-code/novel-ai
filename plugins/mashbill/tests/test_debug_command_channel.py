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
import contextlib
import time

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


async def test_silence_reports_the_named_screen_not_any_screen() -> None:
    """A command names one screen, so the timeout must speak about that screen.

    Reporting when *any* screen last checked in makes a screen that has closed
    read as a live screen whose snippet hung — backwards from the one thing this
    field exists to tell apart.
    """
    async with _async_client() as client:
        await client.get("/api/debug/command?page=alive")  # another screen is up

        gone = (
            await client.post(
                "/api/debug/command", json={"script": "1", "page": "gone", "timeout_ms": 60}
            )
        ).json()
        assert gone["error"] == "timeout"
        assert gone["last_poll_at"] is None, "떠난 화면이 살아 있는 것으로 읽힌다"


async def test_how_long_ago_each_screen_asked_is_listed() -> None:
    """A screen that has closed stays on the list, so the list must say how stale."""
    async with _async_client() as client:
        await client.get("/api/debug/command?page=a")
        listed = (await client.get("/api/debug/pages")).json()["pages"]
        assert listed[0]["seen_ago_s"] >= 0


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


async def test_the_screen_can_wait_for_work_instead_of_asking_again() -> None:
    """Holding the request open lets the screen wait on the network, not a timer.

    Added while chasing O-00000066, on the theory that macOS was stopping the
    viewer's timers behind another window. Measurement later killed that theory
    — 200s occluded slows a 1s timer to about 1.5s and leaves the network alone
    — so this is not the fix it was meant to be. It stays because holding the
    request beats a bare poll either way: work reaches the screen the moment it
    arrives instead of on the next tick.
    """
    async with _async_client() as client:

        async def ask_later() -> None:
            await asyncio.sleep(0.15)
            await client.post("/api/debug/command", json={"script": "1", "timeout_ms": 2000})

        waiting = client.get("/api/debug/command?wait_ms=2000")
        taken, _ = await asyncio.gather(waiting, ask_later())

    assert taken.json()["script"] == "1"


async def test_waiting_gives_up_and_says_nothing_arrived() -> None:
    """The screen must get an answer either way, or its loop stalls."""
    async with _async_client() as client:
        r = await client.get("/api/debug/command?wait_ms=60")
    assert r.status_code == 200
    assert r.json() == {}


async def test_asking_without_waiting_still_answers_at_once() -> None:
    """The old shape keeps working — an agent poking the channel by hand."""
    async with _async_client() as client:
        r = await client.get("/api/debug/command")
    assert r.status_code == 200
    assert r.json() == {}


async def test_waiting_does_not_return_at_once_after_work_was_taken() -> None:
    """The "work is here" flag must come down once the work is taken.

    A screen that waits and is answered at once re-asks at once, which spins it
    against the engine as fast as the network allows — the built app locked up
    that way and stopped answering entirely.
    """
    async with _async_client() as client:
        asking = asyncio.create_task(
            client.post("/api/debug/command", json={"script": "1", "timeout_ms": 2000})
        )
        await asyncio.sleep(0.05)
        taken = (await client.get("/api/debug/command?page=a&wait_ms=500")).json()
        assert taken["script"] == "1"
        await client.post("/api/debug/result", json={"id": taken["id"], "ok": True, "value": 1})
        await asking

        started = time.monotonic()
        assert (await client.get("/api/debug/command?page=a&wait_ms=300")).json() == {}
        assert time.monotonic() - started > 0.2, "일감을 가져간 뒤에도 안 기다리고 바로 돌아왔다"


async def test_waiting_does_not_return_at_once_after_a_command_for_another_screen() -> None:
    """Same flag, the other way it stays up: work aimed elsewhere, then gone."""
    async with _async_client() as client:
        asking = asyncio.create_task(
            client.post("/api/debug/command", json={"script": "1", "page": "a", "timeout_ms": 300})
        )
        await asyncio.sleep(0.05)
        assert (await client.get("/api/debug/command?page=b&wait_ms=60")).json() == {}
        await asking

        started = time.monotonic()
        assert (await client.get("/api/debug/command?page=b&wait_ms=300")).json() == {}
        assert time.monotonic() - started > 0.2, "안 기다리고 바로 돌아왔다"


async def test_an_asker_that_goes_away_does_not_wedge_the_channel() -> None:
    """The waiting command must be dropped when the asker disappears.

    An agent that gives up (its own timeout, a dropped connection) cancels the
    request. Cleanup used to live only on the timeout path, so the command
    stayed armed forever and every later ask got 409 — the channel locked and
    the only way out was restarting the engine. This wedged the channel
    repeatedly before it was understood.
    """
    async with _async_client() as client:
        asking = asyncio.create_task(
            client.post("/api/debug/command", json={"script": "1", "timeout_ms": 30000})
        )
        await asyncio.sleep(0.05)
        asking.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await asking
        await asyncio.sleep(0.05)

        second = await client.post("/api/debug/command", json={"script": "2", "timeout_ms": 60})
        assert second.status_code != 409, "떠난 요청이 통로를 잠갔다"


async def test_a_taken_command_that_is_never_answered_does_not_wedge() -> None:
    """The screen may take work and never report back — it reloaded, it crashed,
    the user closed the window. The asker's own deadline must still free the
    channel.
    """
    async with _async_client() as client:
        asking = asyncio.create_task(
            client.post("/api/debug/command", json={"script": "1", "timeout_ms": 200})
        )
        await asyncio.sleep(0.05)
        taken = (await client.get("/api/debug/command?page=a")).json()
        assert taken["script"] == "1"  # the screen took it
        await asking  # and never answered
        await asyncio.sleep(0.05)

        second = await client.post("/api/debug/command", json={"script": "2", "timeout_ms": 60})
        assert second.status_code != 409, "답 없이 가져간 일감이 통로를 잠갔다"


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
