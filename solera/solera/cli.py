"""The Solera command line — the deterministic surface an agent drives.

Skills instruct the external agent to run ``python -m solera <command>``. Each
command is a thin wrapper over the core: planning, the supervisor, the gate, and
note-writing. The CLI holds no logic of its own and never builds anything.

``--root`` is the project directory: gates run there and ``.noory/solera/`` lives
under it. It defaults to the current directory.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .audit import audit_workspace
from .errors import SoleraError
from .formats import Feedback, Retrospective
from .planning import add_action, create_story
from .supervisor import complete, instruction, start_next
from .workspace import Workspace


def _ws(root: Path) -> Workspace:
    return Workspace(root / ".noory" / "solera")


def _cmd_plan(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    story = create_story(ws, args.goal)
    print(story.id)
    return 0


def _cmd_add(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    action = add_action(ws, args.story, args.goal, gate=args.gate)
    print(action.id)
    return 0


def _cmd_next(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    pair = start_next(ws)
    if pair is None:
        print("(nothing open)")
        return 0
    print(instruction(ws, *pair))
    return 0


def _cmd_complete(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    prog = ws.load_progress()
    if prog.story is None or prog.action is None:
        print("nothing in progress; run 'next' first")
        return 1
    result = complete(ws, prog.story, prog.action, cwd=root)
    if result.passed:
        print(f"PASS {prog.story}/{prog.action}")
        return 0
    print(f"FAIL {prog.story}/{prog.action}")
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print(result.stderr.rstrip())
    return 1


def _cmd_status(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    if ws.progress_path.exists():
        prog = ws.load_progress()
        print(f"pointer: story={prog.story} action={prog.action}")
    else:
        print("pointer: (none)")
    problems = audit_workspace(ws)
    for problem in problems:
        print(f"problem[{problem.kind}]: {problem.detail}")
    return 1 if problems else 0


def _cmd_retro(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    ws.write_retrospective(Retrospective(id=args.story, about=list(args.about), body=args.body))
    return 0


def _cmd_feedback(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    ws.write_feedback(Feedback(id=args.id, about=list(args.about), body=args.body))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solera", description="A slim harness over .noory/solera/"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project directory")
    sub = parser.add_subparsers(dest="command", required=True)

    p_plan = sub.add_parser("plan", help="create a Story from a goal")
    p_plan.add_argument("goal")
    p_plan.set_defaults(func=_cmd_plan)

    p_add = sub.add_parser("add", help="add an Action to a Story")
    p_add.add_argument("story")
    p_add.add_argument("goal")
    p_add.add_argument("--gate", required=True, help="command that verifies the Action")
    p_add.set_defaults(func=_cmd_add)

    p_next = sub.add_parser("next", help="start the next Action and print its instruction")
    p_next.set_defaults(func=_cmd_next)

    p_complete = sub.add_parser("complete", help="run the current Action's gate")
    p_complete.set_defaults(func=_cmd_complete)

    p_status = sub.add_parser("status", help="show the pointer and any audit problems")
    p_status.set_defaults(func=_cmd_status)

    p_retro = sub.add_parser("retro", help="write a Story retrospective")
    p_retro.add_argument("story")
    p_retro.add_argument("body")
    p_retro.add_argument("--about", action="append", default=[], help="id tag (repeatable)")
    p_retro.set_defaults(func=_cmd_retro)

    p_feedback = sub.add_parser("feedback", help="write a blocking feedback note")
    p_feedback.add_argument("id")
    p_feedback.add_argument("body")
    p_feedback.add_argument("--about", action="append", default=[], help="id tag (repeatable)")
    p_feedback.set_defaults(func=_cmd_feedback)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)
    try:
        result: int = args.func(_ws(root), root, args)
    except SoleraError as exc:
        print(f"error: {exc}")
        return 1
    return result
