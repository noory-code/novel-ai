"""The Proof command line — record and query decisions.

``--root`` is the project directory; the log lives at ``.noory/proof/`` under it.
A decision's body (the prose) is passed with ``--body`` or piped on stdin.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .errors import ProofError
from .log import Log


def _log(root: Path) -> Log:
    return Log(root / ".noory" / "proof")


def _cmd_record(log: Log, args: argparse.Namespace) -> int:
    body = args.body if args.body is not None else sys.stdin.read()
    decision = log.record(
        args.title,
        body,
        status=args.status,
        supersedes=args.supersedes,
        about=list(args.about),
    )
    print(decision.id)
    return 0


def _cmd_list(log: Log, args: argparse.Namespace) -> int:
    for decision in log.decisions():
        print(f"{decision.id}  [{decision.status}]  {decision.title}")
    return 0


def _cmd_in_force(log: Log, args: argparse.Namespace) -> int:
    for decision in log.in_force(about=args.about):
        print(f"{decision.id}  {decision.title}")
    return 0


def _cmd_check(log: Log, args: argparse.Namespace) -> int:
    """Gate command: exit 0 if an in-force decision tags ``--about``, else 1."""
    matches = log.in_force(about=args.about)
    for decision in matches:
        print(decision.id)
    return 0 if matches else 1


def _cmd_show(log: Log, args: argparse.Namespace) -> int:
    decision = log.get(args.id)
    print(f"# {decision.id}  [{decision.status}]  {decision.title}")
    if decision.supersedes:
        print(f"supersedes: {decision.supersedes}")
    print()
    print(decision.body)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="proof", description="An append-only decision log.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project directory")
    sub = parser.add_subparsers(dest="command", required=True)

    p_record = sub.add_parser("record", help="append a new decision")
    p_record.add_argument("title")
    p_record.add_argument("--status", choices=["proposed", "accepted"], default="accepted")
    p_record.add_argument("--supersedes", default=None, help="id of a decision this replaces")
    p_record.add_argument("--body", default=None, help="decision prose (else read from stdin)")
    p_record.add_argument(
        "--about", action="append", default=[], help="id this is about (repeatable)"
    )
    p_record.set_defaults(func=_cmd_record)

    p_list = sub.add_parser("list", help="list every decision")
    p_list.set_defaults(func=_cmd_list)

    p_in_force = sub.add_parser("in-force", help="list decisions still in force")
    p_in_force.add_argument("--about", default=None, help="only those tagging this id")
    p_in_force.set_defaults(func=_cmd_in_force)

    p_check = sub.add_parser("check", help="gate: exit 0 if an in-force decision tags --about")
    p_check.add_argument("--about", required=True, help="the id a decision must be about")
    p_check.set_defaults(func=_cmd_check)

    p_show = sub.add_parser("show", help="print one decision")
    p_show.add_argument("id")
    p_show.set_defaults(func=_cmd_show)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result: int = args.func(_log(Path(args.root)), args)
    except ProofError as exc:
        print(f"error: {exc}")
        return 1
    return result
