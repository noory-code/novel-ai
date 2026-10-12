"""Who shows a held proposal to the person: the Novel app under the reply, or the coach itself."""

from __future__ import annotations

import os

from mashbill.mcp_registration import IN_APP_COACH_ENV


def show_instruction(subject: str) -> str:
    """The ``show`` value a proposal tool returns for ``subject`` (for example "draft")."""
    if os.environ.get(IN_APP_COACH_ENV) == "1":
        return (
            f"The app shows this {subject} below your reply; do not restate it. "
            "Ask the person to confirm it or say what to change."
        )
    return f"Show the person this {subject} as written and ask them to confirm it."
