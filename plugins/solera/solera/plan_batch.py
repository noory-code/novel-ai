"""Atomic confirmed-tree planning and request-id replay records."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .errors import (
    FormatError,
    InvalidPlanError,
    ParentIsLeafError,
    PlanningValueError,
    RequestIdConflictError,
    UnknownParentError,
)
from .formats import WorkItem
from .graph import load_items, order_problems
from .planning import (
    _next_item_id_from_ids,
    _raise_order_problems,
    _validate_plain_words,
    _validate_realizes,
    _validated_item,
    assert_items_not_frozen,
    assert_person_edit_allowed,
)
from .workspace import Workspace, _atomic_write_text, workspace_locked


def _plan_records(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        records = json.loads(path.read_text())
        if not isinstance(records, dict):
            raise ValueError("plans.json must be an object")
        for request_id, record in records.items():
            if (
                not isinstance(request_id, str)
                or not isinstance(record, dict)
                or set(record) != {"body", "created"}
                or not isinstance(record["body"], str)
                or not isinstance(record["created"], dict)
                or not all(
                    isinstance(key, str) and isinstance(item_id, str)
                    for key, item_id in record["created"].items()
                )
            ):
                raise ValueError("plans.json has an invalid request record")
        return records
    except (OSError, ValueError) as exc:
        raise FormatError(f"invalid plans.json: {exc}") from exc


@workspace_locked
def create_plan(ws: Workspace, body: dict[str, Any]) -> tuple[bool, dict[str, str], list[WorkItem]]:
    """Validate and commit a confirmed tree with request-id replay protection."""
    record_path = ws.root / "plans.json"
    records = _plan_records(record_path)
    request_id: str = body["request_id"]
    digest = hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    previous = records.get(request_id)
    if previous is not None:
        if previous["body"] != digest:
            raise RequestIdConflictError(f"request_id {request_id!r} has a different body")
        recorded_created = previous["created"]
        return (
            False,
            recorded_created,
            [ws.load_item(item_id) for item_id in recorded_created.values()],
        )

    parent_id: str | None = body["parent"]
    items = load_items(ws)
    parent = items.get(parent_id) if parent_id is not None else None
    if parent_id is not None and parent is None:
        raise UnknownParentError(f"unknown work item: {parent_id}")
    if parent is not None:
        assert_person_edit_allowed(items, [parent.id])
        assert_items_not_frozen(items, [parent.id])

    created: dict[str, str] = {}
    nodes: list[tuple[dict[str, Any], str, str | None, str]] = []
    used_ids = ws.list_items()

    def allocate(node: dict[str, Any], parent_key: str | None, level: str) -> None:
        key = node["key"]
        if not key.strip() or key in created:
            raise InvalidPlanError(f"blank or duplicate plan key: {key!r}")
        if node["accept"] == "children" and not node.get("children"):
            raise InvalidPlanError(f"{key!r} needs at least one child")
        item_id = _next_item_id_from_ids(used_ids, level)
        used_ids.append(item_id)
        created[key] = item_id
        nodes.append((node, key, parent_key, level))
        for child in node.get("children", []):
            allocate(child, key, "action")

    for root in body["items"]:
        allocate(root, None, "story" if parent is None else "action")

    new_items: list[WorkItem] = []
    for node, key, _parent_key, level in nodes:
        after_keys = node.get("after_keys", [])
        if any(after_key not in created for after_key in after_keys):
            raise InvalidPlanError(f"{key!r} names an unknown after_keys entry")
        realizes = node.get("realizes", [])
        _validate_realizes(realizes)
        plain_words = {
            name: node.get(name, [])
            for name in ("conditions", "pass_examples", "fail_examples", "risks", "basis")
        }
        _validate_plain_words(plain_words)
        children = [created[child["key"]] for child in node.get("children", [])]
        item = _validated_item(
            {
                "id": created[key],
                "level": level,
                "status": "todo",
                "goal": node["goal"],
                "accept": node["accept"],
                "children": children,
                "realizes": realizes,
                "after": [*node.get("after", []), *(created[k] for k in after_keys)],
                **plain_words,
            }
        )
        items[item.id] = item
        new_items.append(item)

    updated_parent: WorkItem | None = None
    if parent is not None:
        root_ids = [created[node["key"]] for node in body["items"]]
        try:
            updated_parent = WorkItem.model_validate(
                {**parent.model_dump(), "children": [*parent.children, *root_ids]}
            )
        except ValidationError as exc:
            if parent.gate:
                raise ParentIsLeafError(str(exc)) from exc
            raise PlanningValueError(str(exc)) from exc
        items[parent.id] = updated_parent
    _raise_order_problems(order_problems(items))

    parent_path = ws.item_path(parent.id) if parent is not None else None
    parent_bytes = parent_path.read_bytes() if parent_path is not None else None
    record_bytes = record_path.read_bytes() if record_path.is_file() else None
    try:
        for item in new_items:
            ws.write_item(item)
        if updated_parent is not None:
            ws.write_item(updated_parent)
        records[request_id] = {"body": digest, "created": created}
        _atomic_write_text(
            record_path, json.dumps(records, ensure_ascii=False, separators=(",", ":"))
        )
    except BaseException:
        for item in new_items:
            ws.item_path(item.id).unlink(missing_ok=True)
        if parent_path is not None and parent_bytes is not None:
            _atomic_write_text(parent_path, parent_bytes)
        if record_bytes is None:
            record_path.unlink(missing_ok=True)
        else:
            _atomic_write_text(record_path, record_bytes)
        raise
    return True, created, new_items
