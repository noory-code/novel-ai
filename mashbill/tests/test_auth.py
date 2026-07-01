"""Engine auth seam tests (D-2026-06-12-F, Track 3.5).

Pins three layers:

  1. Pure helpers — ``configured_token`` reads env every call,
     ``extract_bearer`` is case-insensitive + whitespace-tolerant,
     ``is_authorized`` is constant-time and treats ``expected is None`` as
     "auth disabled".
  2. Middleware — env unset → pass-through, env set → 401 on missing /
     invalid token, 200 on good token. /api/health is always open. Non
     /api paths skip the middleware (covers / + the viewer static mount).
  3. WS handler — ``check_ws_token`` mirrors the HTTP rules so the WS
     room can't be subscribed without a token when enforcement is on.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from mashbill.auth import (
    ENV_VAR,
    check_ws_token,
    configured_token,
    extract_bearer,
    is_authorized,
)
from mashbill.broadcast import BroadcastHub
from mashbill.http_app import create_http_app

# ---------------------------------------------------------------------------
# Env fixture — clears MASHBILL_AUTH_TOKEN between tests so a leaked value
# from one case never wedges another.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_auth_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.delenv(ENV_VAR, raising=False)
    yield


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def test_configured_token_returns_none_when_env_unset() -> None:
    assert configured_token() is None


def test_configured_token_returns_value_when_env_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_VAR, "tok-abc")
    assert configured_token() == "tok-abc"


def test_configured_token_treats_blank_and_whitespace_as_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_VAR, "   ")
    assert configured_token() is None


def test_extract_bearer_pulls_token_from_clean_header() -> None:
    assert extract_bearer("Bearer abc123") == "abc123"


def test_extract_bearer_is_case_insensitive_on_scheme() -> None:
    assert extract_bearer("bearer xyz") == "xyz"
    assert extract_bearer("BEARER xyz") == "xyz"


def test_extract_bearer_strips_whitespace_and_handles_missing() -> None:
    assert extract_bearer("  Bearer   tok  ") == "tok"
    assert extract_bearer(None) is None
    assert extract_bearer("") is None
    assert extract_bearer("Token foo") is None  # wrong scheme
    assert extract_bearer("Bearer") is None  # no token after scheme


def test_is_authorized_allows_everything_when_expected_is_none() -> None:
    assert is_authorized(None, None) is True
    assert is_authorized("anything", None) is True


def test_is_authorized_rejects_missing_or_wrong_when_expected_set() -> None:
    assert is_authorized(None, "secret") is False
    assert is_authorized("", "secret") is False
    assert is_authorized("wrong", "secret") is False
    assert is_authorized("secret", "secret") is True


# ---------------------------------------------------------------------------
# Middleware — exercised via the real Starlette app + TestClient
# ---------------------------------------------------------------------------


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    return ws


def _client() -> TestClient:
    return TestClient(create_http_app(hub=BroadcastHub(enable_watchers=False)))


def test_middleware_disabled_when_env_unset_no_token_required(
    workspace: Path,
) -> None:
    client = _client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    # /api/workspace/projects also reachable without a header — this is the
    # v0.64.x baseline behaviour, preserved when env is unset.
    resp2 = client.get(
        "/api/workspace/projects", params={"project_path": str(workspace)}
    )
    # The endpoint may return 200 or any non-401 code (depends on workspace
    # contents); the point of this assertion is "auth didn't reject it".
    assert resp2.status_code != 401


def test_middleware_401_on_missing_header_when_env_set(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_VAR, "secret-tok")
    client = _client()
    resp = client.get(
        "/api/workspace/projects", params={"project_path": str(workspace)}
    )
    assert resp.status_code == 401
    assert "required" in resp.json()["error"]


def test_middleware_401_on_wrong_token(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_VAR, "secret-tok")
    client = _client()
    resp = client.get(
        "/api/workspace/projects",
        params={"project_path": str(workspace)},
        headers={"Authorization": "Bearer nope"},
    )
    assert resp.status_code == 401
    assert "invalid" in resp.json()["error"]


def test_middleware_passes_through_with_correct_token(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_VAR, "secret-tok")
    client = _client()
    resp = client.get(
        "/api/workspace/projects",
        params={"project_path": str(workspace)},
        headers={"Authorization": "Bearer secret-tok"},
    )
    # Not 401 → middleware accepted the token. The body shape is the
    # endpoint's concern.
    assert resp.status_code != 401


def test_health_endpoint_is_always_open(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The Tauri shell probes /api/health before injecting the token; if
    auth blocked /health it could never bootstrap. The open-path list is
    intentionally tiny (only /api/health)."""
    monkeypatch.setenv(ENV_VAR, "secret-tok")
    client = _client()
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_debug_channel_open_without_token_in_debug_flavor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The dev-only debug channel (``/api/debug``, registered only under
    MASHBILL_DEBUG=1) must stay callable WITHOUT the auth token: the viewer's debug
    probe POSTs snapshots with a plain fetch and the agent GETs them — neither
    carries the per-launch token. The auth seam (added later) must not break the
    WKWebView introspection bridge (D-2026-06-23-C)."""
    monkeypatch.setenv("MASHBILL_DEBUG", "1")
    monkeypatch.setenv(ENV_VAR, "secret-tok")
    client = _client()  # built with MASHBILL_DEBUG=1 → /api/debug is registered
    # POST a snapshot with NO Authorization header → accepted (probe is unauthed).
    post = client.post("/api/debug", json={"ts": 1, "theme": "dark", "nodeCount": 0, "nodes": []})
    assert post.status_code == 200
    # GET it back with NO token → 200 (not 401), so the agent can read the screen.
    got = client.get("/api/debug")
    assert got.status_code == 200


# ---------------------------------------------------------------------------
# WS auth — exercised at the helper level. The full WS handshake is e2e and
# not flake-friendly under TestClient + asyncio + monkeypatched env, so we
# verify the helper that the handler calls.
# ---------------------------------------------------------------------------


def test_check_ws_token_allows_anything_when_env_unset() -> None:
    assert check_ws_token(None) is True
    assert check_ws_token("anything") is True


def test_check_ws_token_requires_match_when_env_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(ENV_VAR, "secret")
    assert check_ws_token(None) is False
    assert check_ws_token("") is False
    assert check_ws_token("wrong") is False
    assert check_ws_token("secret") is True


# ---------------------------------------------------------------------------
# Hardening — make sure the env reads cleanly under all-blank shells
# (some CI runners pre-export MASHBILL_AUTH_TOKEN= to test the env-unset path).
# ---------------------------------------------------------------------------


def test_env_var_name_is_documented_constant() -> None:
    """Centralised constant — Tauri + bundled docs reference this string."""
    assert ENV_VAR == "MASHBILL_AUTH_TOKEN"
    # And os.environ uses string keys.
    assert isinstance(os.environ.get(ENV_VAR, ""), str)
