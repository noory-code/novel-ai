"""Environment contract for an in-app coach turn's chat scope.

An in-app coach turn's tool server carries its scope in
``MASHBILL_CHAT_SCOPE``. A feature's flow and its check require that
feature's canvas to be open; a service's check requires the Services canvas.
Writes from other in-app turn scopes are refused (W-00000489). An outside
agent's tool server has no scope and is not restricted.
"""

from __future__ import annotations

import os

CHAT_SCOPE_ENV = "MASHBILL_CHAT_SCOPE"

_OPEN_FEATURE = (
    "Ask the person to open that feature's canvas (click its node on the Services "
    "canvas) and continue there."
)


def effective_chat_scope(chat_scope: str) -> str:
    """Prefer the in-app server environment, then an explicit tool argument."""
    return os.environ.get(CHAT_SCOPE_ENV, "") or chat_scope


def _turn_scope() -> str:
    # Only the in-app server's environment restricts a write; a tool argument
    # (an outside agent may pass one) does not.
    return os.environ.get(CHAT_SCOPE_ENV, "")


def refuse_foreign_flow_write(feature_id: str) -> None:
    """Raise unless this turn may change ``feature_id``'s flow."""
    scope = _turn_scope()
    if scope and scope != f"feature:{feature_id}":
        raise ValueError(
            f"this turn is in the {scope!r} tab; the flow of feature {feature_id!r} "
            f"is drawn only while that feature's canvas is open. {_OPEN_FEATURE}"
        )


def refuse_foreign_check(node_id: str, node_kind: str) -> None:
    """Raise unless this turn may record the design check of ``node_id``."""
    scope = _turn_scope()
    if not scope:
        return
    if node_kind == "feature" and scope != f"feature:{node_id}":
        raise ValueError(
            f"this turn is in the {scope!r} tab; the check of feature {node_id!r} "
            f"is recorded only while that feature's canvas is open. {_OPEN_FEATURE}"
        )
    if node_kind == "service" and scope not in ("services", f"service:{node_id}"):
        raise ValueError(
            f"this turn is in the {scope!r} tab; the check of service {node_id!r} "
            "is recorded only while the Services canvas is open. Ask the person to open "
            "the Services canvas and continue there."
        )
