"""End-to-end integration tests for solera-map.

These tests spawn the actual solera_mcp HTTP server as a subprocess and
drive it over a real TCP socket — complementing test_server.py (which
uses Starlette's TestClient against the same app object in-process).

Scope the E2E suite covers that the in-process tests cannot:

- The `python -m solera_mcp` entry point starts and binds to a port.
- SOLERA_MAP_NO_MCP=1 correctly disables the stdio MCP task so the server
  comes up on HTTP-only (the VSCode extension relies on this).
- SOLERA_MAP_PORT override is honoured.
- SIGTERM terminates the process cleanly (no zombie).
- /api/health responds over real TCP (not just TestClient's in-process path).
- /api/graph returns real file content parsed by real build_graph.
- POST /api/concept/propose-from-narrative writes a real file to disk and
  the Moment-1 guardrail copy is present in the output.

Runtime cost: each test spawns a subprocess, waits ~500ms for bind, then
cleans up. Running the full suite adds ~10s total. If SOLERA_MAP_E2E_SKIP
is set, the module is skipped (useful in constrained CI environments).
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

# Skip entirely if the user opts out (e.g. on a sandboxed CI without network).
pytestmark = pytest.mark.skipif(
    os.environ.get("SOLERA_MAP_E2E_SKIP") is not None,
    reason="SOLERA_MAP_E2E_SKIP is set",
)


def _find_free_port() -> int:
    """Grab an ephemeral port and close immediately. Small race window with the
    server's own bind, but good enough in practice and avoids hard-coding 5170
    (which may already be in use from a running Claude Code instance)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _http_get(url: str, timeout: float = 2.0) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, (json.loads(body) if body else {})
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, (json.loads(body) if body else {})


def _http_post(url: str, body: dict[str, Any], timeout: float = 2.0) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read().decode("utf-8")
            return resp.status, (json.loads(payload) if payload else {})
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        return exc.code, (json.loads(payload) if payload else {})


def _wait_for_health(port: int, deadline_sec: float = 10.0) -> bool:
    """Poll /api/health every 100ms up to deadline. Returns True once healthy."""
    url = f"http://127.0.0.1:{port}/api/health"
    end = time.monotonic() + deadline_sec
    while time.monotonic() < end:
        try:
            status, body = _http_get(url, timeout=0.5)
            if status == 200 and body.get("status") == "ok":
                return True
        except (ConnectionRefusedError, OSError, urllib.error.URLError):
            pass
        time.sleep(0.1)
    return False


def _seed_solera_workspace(base: Path) -> None:
    """Write a minimal but realistic .solera/ layout the server can parse."""
    root = base / ".solera"
    (root / "concepts").mkdir(parents=True, exist_ok=True)
    (root / "roles").mkdir(parents=True, exist_ok=True)
    (root / "personas").mkdir(parents=True, exist_ok=True)
    (root / "journeys").mkdir(parents=True, exist_ok=True)
    (root / "narratives").mkdir(parents=True, exist_ok=True)

    (root / "concepts" / "auth.md").write_text(
        "---\nid: auth\nname: Auth\nstatus: active\n---\n\n"
        "# Intent\nUser proves identity.\n\n"
        "# Current Design\nPasswordless.\n\n"
        "# Current Shape\n(no Stories)\n",
        encoding="utf-8",
    )
    (root / "roles" / "cafe-owner.md").write_text(
        "---\nid: cafe-owner\nkind: role\nname: Cafe Owner\nstatus: active\n"
        "created: 2026-04-19\n---\n\n"
        "# Description\nA small independent cafe owner.\n",
        encoding="utf-8",
    )
    (root / "personas" / "alice.md").write_text(
        "---\nid: alice\nkind: persona\nname: Alice\nstatus: active\n"
        "role: cafe-owner\ncreated: 2026-04-19\n---\n\n"
        "# Identity\nAlice runs a small cafe.\n\n"
        "# Goals\n- Sell more coffee\n",
        encoding="utf-8",
    )
    (root / "narratives" / "rush-orders.md").write_text(
        "---\nid: rush-orders\nkind: narrative\nform: user_story\n"
        "status: active\ncreated: 2026-04-19\n"
        'about_roles: ["cafe-owner"]\n'
        'about_personas: ["alice"]\n---\n\n'
        "# Statement\nAs a cafe owner, I want rush orders tracked.\n\n"
        "# Context\nMornings are chaotic.\n\n"
        "# Acceptance Cues\n- Orders arrive within 1s.\n",
        encoding="utf-8",
    )


def _spawn_server(project_path: Path, port: int, skip_mcp: bool = True) -> subprocess.Popen[bytes]:
    env = os.environ.copy()
    env["SOLERA_MAP_PORT"] = str(port)
    if skip_mcp:
        env["SOLERA_MAP_NO_MCP"] = "1"
    # On POSIX we start a new session so kill propagates to the whole group.
    kwargs: dict[str, Any] = {
        "env": env,
        "cwd": str(project_path),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
    }
    if sys.platform != "win32":
        kwargs["start_new_session"] = True
    else:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    return subprocess.Popen(
        [sys.executable, "-m", "solera_mcp"],
        **kwargs,
    )


def _kill_server(proc: subprocess.Popen[bytes]) -> None:
    """SIGTERM the process group (or the process on Windows); fall back to kill."""
    if proc.poll() is not None:
        return
    try:
        if sys.platform != "win32":
            os.killpg(proc.pid, signal.SIGTERM)
        else:
            proc.terminate()
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if sys.platform != "win32":
            os.killpg(proc.pid, signal.SIGKILL)
        else:
            proc.kill()
        proc.wait(timeout=2)


@pytest.fixture
def live_server(tmp_path: Path) -> Any:
    """Spawn a real solera_mcp server against a seeded .solera/ workspace."""
    _seed_solera_workspace(tmp_path)
    port = _find_free_port()
    proc = _spawn_server(tmp_path, port, skip_mcp=True)
    try:
        if not _wait_for_health(port):
            # Capture server output so the test reports the failure reason.
            _kill_server(proc)
            stdout, stderr = proc.communicate(timeout=2)
            raise RuntimeError(
                "server failed to start within 10s.\n"
                f"stdout: {stdout.decode('utf-8', 'replace')}\n"
                f"stderr: {stderr.decode('utf-8', 'replace')}"
            )
        yield {"port": port, "project_path": tmp_path, "proc": proc}
    finally:
        _kill_server(proc)


# ---------------------------------------------------------------------------
# Startup / binding
# ---------------------------------------------------------------------------


def test_server_starts_on_assigned_port_with_mcp_disabled(live_server: dict[str, Any]) -> None:
    """SOLERA_MAP_NO_MCP=1 lets the server come up HTTP-only (no stdio).

    The VSCode extension depends on this — it spawns the server with no
    stdio client, and the MCP task would otherwise hang waiting for a
    peer.
    """
    port = live_server["port"]
    status, body = _http_get(f"http://127.0.0.1:{port}/api/health")
    assert status == 200
    assert body == {"status": "ok", "service": "solera-map"}


def test_graph_endpoint_returns_seeded_entities_over_real_tcp(
    live_server: dict[str, Any],
) -> None:
    """Full-stack read: file → graph.py → Starlette → uvicorn → TCP → client."""
    port = live_server["port"]
    project_path = str(live_server["project_path"])
    status, body = _http_get(
        f"http://127.0.0.1:{port}/api/graph?project_path={project_path}",
        timeout=3.0,
    )
    assert status == 200
    assert [c["id"] for c in body["concepts"]] == ["auth"]
    assert [r["id"] for r in body["roles"]] == ["cafe-owner"]
    assert [p["id"] for p in body["personas"]] == ["alice"]
    assert [n["id"] for n in body["narratives"]] == ["rush-orders"]
    assert body["narratives"][0]["about_roles"] == ["cafe-owner"]
    assert body["narratives"][0]["about_personas"] == ["alice"]


# ---------------------------------------------------------------------------
# propose-from-narrative — the Moment 1 guardrail path
# ---------------------------------------------------------------------------


def test_propose_from_narrative_writes_stub_concept_to_disk(
    live_server: dict[str, Any],
) -> None:
    """The endpoint writes a real Concept file with the Moment 1 guardrail
    in Intent. This is the full round-trip: HTTP → server → file → disk.
    """
    port = live_server["port"]
    project_path: Path = live_server["project_path"]
    status, body = _http_post(
        f"http://127.0.0.1:{port}/api/concept/propose-from-narrative?project_path={project_path}",
        {
            "narrative_id": "rush-orders",
            "concept_id": "order-tracking",
            "concept_name": "Order Tracking",
        },
    )
    assert status == 200
    assert body["ok"] is True
    assert body["needs_intent_review"] is True

    # Stub Concept exists on disk with the exact Moment 1 guardrail copy.
    concept_path = project_path / ".solera" / "concepts" / "order-tracking.md"
    assert concept_path.exists()
    content = concept_path.read_text(encoding="utf-8")
    assert "needs human review per solera-write-concept Moment 1 rule" in content
    assert "id: order-tracking" in content
    assert "name: Order Tracking" in content

    # Narrative's frontmatter gained the new concept_id.
    narrative_content = (project_path / ".solera" / "narratives" / "rush-orders.md").read_text(
        encoding="utf-8"
    )
    assert "order-tracking" in narrative_content

    # Subsequent GET /api/graph returns the new Concept.
    status, graph = _http_get(
        f"http://127.0.0.1:{port}/api/graph?project_path={project_path}",
    )
    assert status == 200
    assert {c["id"] for c in graph["concepts"]} == {"auth", "order-tracking"}


def test_propose_from_narrative_409s_on_duplicate_over_real_tcp(
    live_server: dict[str, Any],
) -> None:
    port = live_server["port"]
    project_path: Path = live_server["project_path"]

    # First attempt writes the stub.
    status, _ = _http_post(
        f"http://127.0.0.1:{port}/api/concept/propose-from-narrative?project_path={project_path}",
        {
            "narrative_id": "rush-orders",
            "concept_id": "auth",  # already exists in the seed
            "concept_name": "Auth (duplicate)",
        },
    )
    assert status == 409


# ---------------------------------------------------------------------------
# Port handling
# ---------------------------------------------------------------------------


def test_server_respects_solera_mcp_port_env(tmp_path: Path) -> None:
    """Override via env var, not the default 5170."""
    _seed_solera_workspace(tmp_path)
    port = _find_free_port()
    # Confirm the port is NOT 5170 (would collide with the default test).
    assert port != 5170, "ephemeral port allocator unexpectedly returned 5170"
    proc = _spawn_server(tmp_path, port, skip_mcp=True)
    try:
        assert _wait_for_health(port), "server did not bind to custom port"
        # Default port should NOT be listening (this also confirms the env
        # override was honoured, not that the server bound to both).
        with pytest.raises((ConnectionRefusedError, OSError, urllib.error.URLError)):
            _http_get("http://127.0.0.1:5170/api/health", timeout=0.3)
    finally:
        _kill_server(proc)


# ---------------------------------------------------------------------------
# Shutdown
# ---------------------------------------------------------------------------


def test_sigterm_during_idle_completes_cleanly(tmp_path: Path) -> None:
    """SIGTERM on an idle server returns within the test timeout, no zombie.

    We deliberately do NOT assert that the port is reusable immediately —
    TCP TIME_WAIT can hold it for 30–60s on some kernels even though the
    server has shut down cleanly. What matters is that the process exits
    and does not become a zombie; the VSCode extension's ServerProcess
    probes /api/health before spawning anyway, so port re-availability
    is not a correctness invariant here.
    """
    _seed_solera_workspace(tmp_path)
    port = _find_free_port()
    proc = _spawn_server(tmp_path, port, skip_mcp=True)
    assert _wait_for_health(port)

    # Send SIGTERM and wait for exit.
    _kill_server(proc)
    assert proc.poll() is not None, "process still running after kill"
    # Exit code should be 0 (graceful) or -SIGTERM (15) depending on Python's
    # signal-handling mode. Either is fine; we only care that it died.
    assert proc.returncode in (0, -signal.SIGTERM, signal.SIGTERM), (
        f"unexpected exit code {proc.returncode}"
    )

    # The process is no longer serving — its old port returns connection
    # refused (even while the OS holds it in TIME_WAIT).
    with pytest.raises((ConnectionRefusedError, OSError, urllib.error.URLError)):
        _http_get(f"http://127.0.0.1:{port}/api/health", timeout=0.5)
