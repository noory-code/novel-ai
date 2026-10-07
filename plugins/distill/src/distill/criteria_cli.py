"""JSON command-line interface for project criteria."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, NoReturn

from distill.store.criteria import CriteriaError, CriteriaStore


class CriteriaParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        raise CriteriaError("E_INVALID_REQUEST", message)


def _arguments(args: list[str]) -> argparse.Namespace:
    parser = CriteriaParser(prog="distill criteria", allow_abbrev=False)
    commands = parser.add_subparsers(dest="action", required=True)
    for name in ("record", "revise", "revoke", "current", "check", "history"):
        command = commands.add_parser(name, allow_abbrev=False)
        command.add_argument("--db", type=Path)
        if name in {"revise", "revoke", "history"}:
            command.add_argument("criterion_id")
        if name in {"record", "revise", "revoke"}:
            command.add_argument("--payload-file", required=True, type=Path)
            command.add_argument("--idempotency-key", required=True)
        if name in {"current", "check"}:
            command.add_argument("--project", required=True)
        if name == "check":
            command.add_argument("--refs", required=True)
    return parser.parse_args(args)


def _payload(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CriteriaError("E_INVALID_REQUEST", f"Cannot read payload file: {error}") from error
    if not isinstance(data, dict):
        raise CriteriaError("E_INVALID_REQUEST", "Payload must be a JSON object")
    return data


def _execute(args: list[str]) -> dict[str, Any]:
    parsed = _arguments(args)
    store = CriteriaStore(parsed.db)
    if parsed.action == "record":
        return store.record(_payload(parsed.payload_file), idempotency_key=parsed.idempotency_key)
    if parsed.action == "revise":
        return store.revise(
            parsed.criterion_id,
            _payload(parsed.payload_file),
            idempotency_key=parsed.idempotency_key,
        )
    if parsed.action == "revoke":
        return store.revoke(
            parsed.criterion_id,
            _payload(parsed.payload_file),
            idempotency_key=parsed.idempotency_key,
        )
    if parsed.action == "current":
        return store.current(parsed.project)
    if parsed.action == "check":
        refs = [reference.strip() for reference in parsed.refs.split(",") if reference.strip()]
        if not refs:
            raise CriteriaError("E_INVALID_REQUEST", "--refs must contain a reference")
        return store.check(parsed.project, refs)
    return store.history(parsed.criterion_id)


def run_criteria_cli(args: list[str]) -> int:
    """Run one criteria command and print exactly one JSON value."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        output = _execute(args)
    except CriteriaError as error:
        print(json.dumps(error.as_dict(), ensure_ascii=False, sort_keys=True))
        return 3 if error.store_error else 2
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0
