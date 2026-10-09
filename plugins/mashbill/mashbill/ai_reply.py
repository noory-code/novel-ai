"""Read JSON objects from AI replies."""

from __future__ import annotations

import json
import re
from typing import Any


def first_json_object(raw: str) -> dict[str, Any] | None:
    """Read the first decodable JSON object from an AI reply."""
    cleaned = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).replace("```", "")
    decoder = json.JSONDecoder()
    parsed: object | None = None
    for index, char in enumerate(cleaned):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            break
        parsed = None
    return parsed if isinstance(parsed, dict) else None
