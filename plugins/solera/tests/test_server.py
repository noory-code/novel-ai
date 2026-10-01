"""HTTP server configuration."""

from __future__ import annotations

import pytest
import uvicorn

from solera.server import DEFAULT_HTTP_PORT, resolved_port, run_http_only


@pytest.mark.parametrize("value", [None, "", "not-a-port", "0", "65536"])
def test_resolved_port_falls_back_for_missing_or_invalid_values(
    monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv("SOLERA_PORT", raising=False)
    else:
        monkeypatch.setenv("SOLERA_PORT", value)

    assert resolved_port() == DEFAULT_HTTP_PORT


def test_resolved_port_accepts_valid_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOLERA_PORT", "6200")

    assert resolved_port() == 6200


def test_http_runner_binds_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, object]] = []
    monkeypatch.delenv("SOLERA_PORT", raising=False)

    def fake_run(app: object, **kwargs: object) -> None:
        calls.append({"app": app, **kwargs})

    monkeypatch.setattr(uvicorn, "run", fake_run)

    run_http_only()

    assert calls[0]["host"] == "127.0.0.1"
    assert calls[0]["port"] == DEFAULT_HTTP_PORT
