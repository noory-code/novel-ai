"""Record that a coach tool was called, when a run asks us to.

The coach's design discriminators (what makes a value strong, a services map
honest) do not ride in the per-turn prompt — they live behind
``get_design_principles``, which the coach may or may not call
(D-2026-07-03-P). Nothing recorded whether it did, so a plate where the coach
never looked was indistinguishable from one where it looked and the guidance did
not help. W-00000176 changed what the tool says, measured 24 plates, and could
not read the result for exactly that reason (O-00000043).

Opt-in by design: only a simulator run sets ``MASHBILL_TOOL_LOG``. In a user's
own project nothing is written and no path is touched.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

#: Absolute path of a JSONL file to append one line per recorded tool call.
TOOL_LOG_ENV = "MASHBILL_TOOL_LOG"


def record_tool_call(tool: str, **fields: Any) -> None:
    """Append one JSON line about a tool call, if a log path is set.

    Never raises. Recording is for us; the answer is for the founder, and a bad
    path must not end the coach's turn.
    """
    path = os.environ.get(TOOL_LOG_ENV)
    if not path:
        return
    try:
        line = json.dumps({"tool": tool, "ts": time.time(), **fields}, ensure_ascii=False)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        return
