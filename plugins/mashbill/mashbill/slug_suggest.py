"""AI-assisted English id proposals for first-time format-F publication."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from mashbill.ai_reply import first_json_object
from mashbill.format_f import plan_service_release, project_snapshot_nodes
from mashbill.format_f_slugs import (
    SLUG_TAIL_MAX,
    SLUG_TAIL_RE,
    pending_slug_names,
    read_slug_store,
)

SLUG_SUGGEST_TIMEOUT_SECONDS = 60.0

_PROMPT = (
    "You name design nodes for file and folder ids.\n"
    "For each node below, give one short English id that means the same as its name. "
    "Translate the meaning; do not transliterate the sounds.\n"
    "Each id: lowercase ASCII letters and digits in words joined by single hyphens, "
    "1 to 4 words, at most 40 characters, no kind prefix.\n"
    "Examples: 결제하기 (feature) -> checkout; 운영자 (actor) -> operator; "
    "주문 내역 (entity) -> order-history.\n"
    "Return only one JSON object that maps each node_id to its id, with no other text. "
    "Do not use tools.\n"
    "Nodes (JSON):\n"
)

_DESCRIPTION_FIELDS = {
    "feature": "proposed",
    "service": "problem",
    "entity": "summary",
    "core_value": "definition",
    "identity": "description",
    "actor": "body",
}


def build_slug_prompt(rows: list[Any]) -> str:
    payload = []
    for row in rows:
        if isinstance(row, dict):
            node_id = row.get("node_id", row.get("id"))
            kind = row.get("kind")
            label = row.get("label")
            field = _DESCRIPTION_FIELDS.get(str(kind))
            description = str(row.get(field, "") or "")[:200] if field else ""
        else:
            node_id = row.id
            kind = row.kind
            label = row.label
            field = _DESCRIPTION_FIELDS.get(str(kind))
            description = str(getattr(row, field, "") or "")[:200] if field else ""
        payload.append(
            {
                "node_id": node_id,
                "kind": kind,
                "label": label,
                "description": description,
            }
        )
    return _PROMPT + json.dumps(payload, ensure_ascii=False)


def parse_slug_reply(raw: str, node_ids: list[str]) -> dict[str, str]:
    """Read the first JSON object and retain only exact, valid requested ids."""
    parsed = first_json_object(raw)
    if parsed is None:
        return {}

    wanted = set(node_ids)
    result: dict[str, str] = {}
    for node_id, value in parsed.items():
        if (
            isinstance(node_id, str)
            and node_id in wanted
            and isinstance(value, str)
            and len(value) <= SLUG_TAIL_MAX
            and SLUG_TAIL_RE.fullmatch(value)
        ):
            result[node_id] = value
    return result


def _wire_nodes(nodes: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "node_id": node.id,
            "kind": node.kind,
            "label": node.label,
            "proposed": None,
            "deduped": False,
        }
        for node in nodes
    ]


async def slug_proposals(
    plot_root: Path,
    project_id: str,
    scope: str,
    service_id: str | None,
    *,
    suggest: bool,
    provider: Any | None,
    model: str | None,
) -> dict[str, Any]:
    """Return proposal rows without mutating publication or chat-session state."""
    if scope == "project":
        nodes = project_snapshot_nodes(plot_root, project_id)
    elif scope == "service":
        if not service_id:
            raise ValueError("'service_id' is required for service scope")
        nodes = plan_service_release(plot_root, project_id, service_id)
    else:
        raise ValueError("'scope' must be one of project/service")

    needed, taken = pending_slug_names(read_slug_store(plot_root, project_id), nodes)
    rows = _wire_nodes(needed)
    if not needed or not suggest:
        return {"needed": rows, "taken": taken, "ai_status": "skipped"}
    if provider is None:
        return {"needed": rows, "taken": taken, "ai_status": "no_provider"}

    try:
        raw = await asyncio.wait_for(
            provider.complete_once(build_slug_prompt(needed), model=model),
            timeout=SLUG_SUGGEST_TIMEOUT_SECONDS,
        )
    except Exception:
        return {"needed": rows, "taken": taken, "ai_status": "failed"}

    parsed = parse_slug_reply(raw, [node.id for node in needed])
    used = set(taken)
    for node, row in zip(needed, rows, strict=True):
        base = parsed.get(node.id)
        if base is None:
            continue
        tail = base
        full_id = f"{node.kind}/{tail}"
        suffix = 2
        while full_id in used:
            tail = f"{base}-{suffix}"
            full_id = f"{node.kind}/{tail}"
            suffix += 1
        if len(tail) > SLUG_TAIL_MAX:
            continue
        row["proposed"] = tail
        row["deduped"] = tail != base
        used.add(full_id)
    return {"needed": rows, "taken": taken, "ai_status": "ok"}
