"""Environment contract for an in-app coach turn's chat scope."""

from __future__ import annotations

import os

CHAT_SCOPE_ENV = "MASHBILL_CHAT_SCOPE"


def effective_chat_scope(chat_scope: str) -> str:
    """Prefer the in-app server environment, then an explicit tool argument."""
    return os.environ.get(CHAT_SCOPE_ENV, "") or chat_scope
