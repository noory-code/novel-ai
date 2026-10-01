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
from .graph import completion, load_items
from .intake import import_release, load_imported_release
from .notes import record_feedback, record_retrospective
from .planning import (
    add_after,
    create_item,
    move_item,
    remove_after,
    set_after,
    set_goal,
    set_realizes,
)
from .repin import apply_repin, propose_repin
from .supervisor import complete, instruction, ready_leaves, start_next
from .workspace import Workspace, workspace_locked


def _ws(root: Path) -> Workspace:
    return Workspace(root / ".noory" / "solera")


def _cmd_plan(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    print(create_item(ws, args.level, args.goal, after=args.after).id)
    return 0


def _cmd_add(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    item = create_item(
        ws,
        args.level,
        args.goal,
        gate=args.gate,
        parent=args.parent,
        realizes=args.realizes,
        after=args.after,
    )
    print(item.id)
    return 0


def _cmd_next(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    item_id = start_next(ws)
    if item_id is None:
        print("(nothing open)")
        return 0
    print(instruction(ws, item_id))
    return 0


@workspace_locked
def _cmd_complete(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    prog = ws.load_progress()
    if prog.item is None:
        print("nothing in progress; run 'next' first")
        return 1
    result = complete(ws, prog.item, cwd=root)
    if result.passed:
        print(f"PASS {prog.item}")
        return 0
    print(f"FAIL {prog.item}")
    if result.stdout.strip():
        print(result.stdout.rstrip())
    if result.stderr.strip():
        print(result.stderr.rstrip())
    return 1


def _cmd_status(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    if ws.progress_path.exists():
        print(f"pointer: item={ws.load_progress().item}")
    else:
        print("pointer: (none)")
    for item_id, value in completion(load_items(ws)).items():
        percent = f"{value.percent}%" if value.percent is not None else "-"
        print(f"progress: {item_id} {value.done}/{value.total} {percent}")
    problems = audit_workspace(ws)
    for problem in problems:
        print(f"problem[{problem.kind}]: {problem.detail}")
    return 1 if problems else 0


def _cmd_after(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    print(set_after(ws, args.item, list(args.ids)).id)
    return 0


def _cmd_goal(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    print(set_goal(ws, args.item, args.goal).id)
    return 0


def _cmd_realizes(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    print(set_realizes(ws, args.item, list(args.slugs)).id)
    return 0


def _cmd_move(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    print(move_item(ws, args.item, args.parent, args.index).id)
    return 0


def _cmd_link(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    print(add_after(ws, args.item, args.predecessor).id)
    return 0


def _cmd_unlink(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    print(remove_after(ws, args.item, args.predecessor).id)
    return 0


def _cmd_ready(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    ready, blocked = ready_leaves(ws)
    print(f"ready: {', '.join(ready) if ready else '(none)'}")
    for leaf in blocked:
        for reason in leaf.reasons:
            print(f"blocked: {reason}")
    return 0


def _cmd_import(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    """Import a published Novel release (format F) — the pipeline's entry step.
    Copy the ``vS`` service bundle and the ``vP`` snapshot it is ``based_on``
    into ``specs/{label}/``. The user wires in the path mashbill published; Solera
    never reaches into Novel (format-f.md §6 / 04-pipeline)."""
    try:
        manifest = import_release(ws, Path(args.source), label=args.label)
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        raise SoleraError(str(exc)) from exc
    print(f"imported {manifest['service']} {manifest['release']} as specs/{args.label}")
    return 0


def _cmd_repin(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    """Re-pin against a re-published release: diff two imported labels, surface
    which work items go stale / orphan, and (only with ``--apply <proposal_id>``)
    reopen the approved stale ones. ``removed`` slugs escalate to a human and
    are never auto-reopened — the human-in-the-loop gate (04-pipeline)."""
    try:
        old_release = load_imported_release(ws, args.old)
        new_release = load_imported_release(ws, args.new)
        prop = propose_repin(ws, old_release, new_release)
    except (FileNotFoundError, ValueError) as exc:
        raise SoleraError(str(exc)) from exc

    diff = prop["diff"]
    print(f"changed: {diff['changed']}")
    print(f"removed: {diff['removed']}")
    print(f"added:   {diff['added']}")
    shared_diff = prop["shared_diff"]
    print(f"shared changed: {shared_diff['changed']}")
    print(f"shared removed: {shared_diff['removed']}")
    print(f"shared added:   {shared_diff['added']}")
    print(f"refs changed: {prop['refs_changed']}")
    print(f"stale (reopen candidates): {prop['stale']}")
    print(f"escalate (human decision; never auto-reopened): {prop['escalate']}")
    print("reasons:")
    for item_id, reasons in prop["reasons"].items():
        for reason in reasons:
            print(f"  {item_id}: {reason}")
    print(f"proposal: {prop['proposal_id']}")
    if args.apply is not None:
        try:
            applied = apply_repin(ws, old_release, new_release, args.apply)
        except ValueError as exc:
            raise SoleraError(str(exc)) from exc
        print(f"reopened: {applied['reopened']}")
    else:
        print("(proposal only — pass --apply <proposal_id> after human approval)")
    return 0


def _cmd_retro(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    record_retrospective(ws, Retrospective(id=args.item, about=list(args.about), body=args.body))
    return 0


def _cmd_feedback(ws: Workspace, root: Path, args: argparse.Namespace) -> int:
    record_feedback(ws, Feedback(id=args.id, about=list(args.about), body=args.body))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solera", description="A slim harness over .noory/solera/"
    )
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="project directory")
    sub = parser.add_subparsers(dest="command", required=True)

    p_plan = sub.add_parser("plan", help="create a root WorkItem from a goal")
    p_plan.add_argument("goal")
    p_plan.add_argument("--level", default="story", help="initiative/epic/story/action")
    p_plan.add_argument("--after", action="append", default=[], help="required predecessor id")
    p_plan.set_defaults(func=_cmd_plan)

    p_add = sub.add_parser("add", help="add a child WorkItem under a parent")
    p_add.add_argument("parent")
    p_add.add_argument("goal")
    p_add.add_argument("--level", default="action", help="initiative/epic/story/action")
    p_add.add_argument("--gate", default="", help="command that verifies a leaf")
    p_add.add_argument(
        "--realizes",
        action="append",
        default=[],
        help="format F slug this item realizes (repeatable, e.g. feature/login)",
    )
    p_add.add_argument("--after", action="append", default=[], help="required predecessor id")
    p_add.set_defaults(func=_cmd_add)

    p_after = sub.add_parser("after", help="replace a WorkItem's order links")
    p_after.add_argument("item")
    p_after.add_argument("ids", nargs="*")
    p_after.set_defaults(func=_cmd_after)

    p_goal = sub.add_parser("goal", help="replace a WorkItem's goal")
    p_goal.add_argument("item")
    p_goal.add_argument("goal")
    p_goal.set_defaults(func=_cmd_goal)

    p_realizes = sub.add_parser("realizes", help="replace a WorkItem's realizes slugs")
    p_realizes.add_argument("item")
    p_realizes.add_argument("slugs", nargs="*")
    p_realizes.set_defaults(func=_cmd_realizes)

    p_move = sub.add_parser("move", help="reparent or reorder a WorkItem")
    p_move.add_argument("item")
    p_move.add_argument("--parent", help="new parent id; omit to make the item a root")
    p_move.add_argument("--index", type=int, help="zero-based position among new siblings")
    p_move.set_defaults(func=_cmd_move)

    p_link = sub.add_parser("link", help="add one WorkItem order link")
    p_link.add_argument("item")
    p_link.add_argument("predecessor")
    p_link.set_defaults(func=_cmd_link)

    p_unlink = sub.add_parser("unlink", help="remove one WorkItem order link")
    p_unlink.add_argument("item")
    p_unlink.add_argument("predecessor")
    p_unlink.set_defaults(func=_cmd_unlink)

    p_ready = sub.add_parser("ready", help="list ready and blocked todo leaves")
    p_ready.set_defaults(func=_cmd_ready)

    p_next = sub.add_parser("next", help="start the next leaf and print its instruction")
    p_next.set_defaults(func=_cmd_next)

    p_complete = sub.add_parser("complete", help="run the current leaf's gate")
    p_complete.set_defaults(func=_cmd_complete)

    p_status = sub.add_parser("status", help="show the pointer and any audit problems")
    p_status.set_defaults(func=_cmd_status)

    p_import = sub.add_parser(
        "import", help="import a published Novel release (format F vS + its vP) into specs/{label}"
    )
    p_import.add_argument(
        "source", help="path to the published vS bundle dir (…/published/{slug}/vS{N})"
    )
    p_import.add_argument(
        "--label", required=True, help="local spec label to import under (specs/{label})"
    )
    p_import.set_defaults(func=_cmd_import)

    p_repin = sub.add_parser(
        "repin", help="diff two imported releases and reopen stale work by approved proposal ID"
    )
    p_repin.add_argument("old", help="imported release label to diff from (specs/{label})")
    p_repin.add_argument("new", help="imported release label to diff to")
    p_repin.add_argument(
        "--apply",
        metavar="PROPOSAL_ID",
        help="reopen stale items from this human-approved proposal; without it, propose only",
    )
    p_repin.set_defaults(func=_cmd_repin)

    p_retro = sub.add_parser("retro", help="write a retrospective for an item")
    p_retro.add_argument("item")
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
    except (SoleraError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}")
        return 1
    return result
