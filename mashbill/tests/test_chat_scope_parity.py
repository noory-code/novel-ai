"""Engine-side invariants for the ChatScope wire enum (D-2026-06-13-H).

The chat redesign scopes conversations per canvas kind plus one shared
``project`` scope. The scope literal is a cross-cutting wire value: the
viewer sends it on ``POST /api/chat/send`` and demultiplexes incoming
``chat_stream_event`` payloads on it, while the engine keys chat sessions
on it. Both sides must agree on the exact member set.

**Post open-core cut (D-2026-06-20-L / -M):** the TS side moved to the app
repo, so the cross-repo regex parity that read ``viewer/src/types.ts`` is
retired here and re-homed in the app's vitest (``use-chat-stream-scope`` +
the committed wire artifacts). This file now pins the **engine** member set
so neither half can quietly drift from the agreed scopes.
"""

from __future__ import annotations

from typing import get_args

from mashbill.chat_providers.base import ChatScope, is_valid_scope

_EXPECTED_SCOPES = {
    "project",
    "foundation",
    "actors",
    "services",
    "entities",
    "feature",
}


def test_chat_scope_is_project_plus_canvas_kinds() -> None:
    """The scope set is exactly ``project`` + the five canvas kinds
    (foundation / actors / services / entities / feature) — pins the member
    set so neither side can quietly add another."""
    assert set(get_args(ChatScope)) == _EXPECTED_SCOPES


def test_feature_scope_accepts_id_suffix() -> None:
    """Layer 1 (CHAT_ARCH.md): ``feature`` is the one parametric
    member — a wire scope carries the service instance id as
    ``feature:<id>`` so each service gets its own thread."""
    assert is_valid_scope("feature:svc_123")
    assert is_valid_scope("feature:any-id-shape")
    # Singleton base scopes stay valid bare.
    for base in ("project", "foundation", "actors", "services", "entities"):
        assert is_valid_scope(base)
    # An empty id is not a real instance, and a typo is still rejected.
    assert not is_valid_scope("feature:")
    assert not is_valid_scope("bogus")


def test_service_scope_accepts_id_suffix() -> None:
    """Per-service thread (D-2026-06-26-A): ``service`` is a second
    parametric member — selecting a single service keys ``service:<id>``,
    parallel to ``feature:<id>``. Bare ``service`` with no id is rejected
    (Fail Fast), same as bare ``feature``."""
    assert is_valid_scope("service:svc_123")
    assert is_valid_scope("service:any-id-shape")
    assert not is_valid_scope("service:")
