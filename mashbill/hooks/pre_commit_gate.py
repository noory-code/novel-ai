#!/usr/bin/env python3
"""PreToolUse hook for Novel — gate ``git commit`` on type-check + tests.

When the assistant attempts to run ``git commit`` (or ``git push``) and
Novel's viewer or MCP source has staged changes, this hook runs the
relevant checks first:

- ``viewer/`` staged changes ⇒ ``cd plot/viewer && npx tsc --noEmit``
  and ``npx vitest run``.
- ``mashbill/`` staged changes ⇒ ``cd mashbill && uv run pytest``.

If any check fails, the commit is blocked with a permissionDecision
of ``deny`` and the failure output is returned so the assistant can
fix and retry.

Cross-platform via Python stdlib + subprocess. Skips itself when the
staged paths are outside Novel or when no relevant files are staged.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Patterns that, if matched anywhere in the bash command, indicate a
# write to the public history (commit / push) where we want to gate.
GATING_COMMAND_RE = re.compile(
    r"\bgit\s+(commit|push)\b",
    re.IGNORECASE,
)


# Cross-cutting visual SSOT files. Bundling any of these with a
# feature change in one commit is the v0.13.10 anti-pattern (see
# D-2026-05-11-C). Pre-commit gate blocks the bundle; the visual
# fix ships in its own atomic commit with its own D-id.
CROSS_CUTTING_VISUAL_CODE = frozenset({
    "viewer/src/styles.css",
})


def find_plot_root() -> Path | None:
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if plugin_root:
        candidate = Path(plugin_root)
        if (candidate / "viewer").exists() and (candidate / "mashbill").exists():
            return candidate
    here = Path(__file__).resolve()
    for parent in [here.parent.parent, here.parent.parent.parent]:
        if (parent / "viewer").exists() and (parent / "mashbill").exists():
            return parent
    return None


def staged_paths(repo_root: Path) -> list[str]:
    """Return staged file paths (relative to repo root)."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except FileNotFoundError:
        return []


def viewer_changes_staged(staged: list[str], plot_root: Path) -> bool:
    rel = plot_root.name + "/viewer/"
    return any(p.startswith(rel) for p in staged)


def mcp_changes_staged(staged: list[str], plot_root: Path) -> bool:
    rel = plot_root.name + "/mashbill/"
    return any(p.startswith(rel) for p in staged)


def reset_complete_check(
    staged: list[str], plot_root: Path
) -> str | None:
    """Verify the v0.15 structural reset stays complete on every commit
    that touches viewer or server code.

    Returns a deny message when any of the four structural invariants
    pinned by D-2026-05-12-B → -F is violated; returns None when OK.

    The invariants (single boolean = AND of all four):

      1. ``mashbill/models.py`` defines ``SketchNode`` as an
         ``Annotated[Union[...], Field(discriminator="kind")]`` — i.e.
         the 15-way discriminated union, not a god class.
      2. ``viewer/src/canvases/SketchInspector.tsx`` absent from disk
         (deleted in v0.15.0, Phase 2.10).
      3. ``viewer/src/canvases/SketchNode.tsx`` absent from disk
         (deleted in v0.15.5, Phase 3.5).
      4. Zero ``canvas_kind ===`` / ``canvas_kind !==`` / ``switch
         (canvas_kind`` branching in ``viewer/src/canvases/sketch/``
         — wrappers supply canvas-specific behaviour via props, not
         the transforms branching on canvas kind.

    Docs-only and other non-viewer/non-server commits skip the check.
    """
    if not (viewer_changes_staged(staged, plot_root) or mcp_changes_staged(staged, plot_root)):
        return None

    failures: list[str] = []

    # 1) Server: SketchNode is the 15-way discriminated union. The union body
    # may live in any module under ``mashbill/`` — models.py is a facade since
    # the v0.59.3 split (D-2026-06-11-B).
    # Match both forms the codebase + tests use:
    #   SketchNode = Annotated[Union[...], Field(discriminator="kind")]
    #   SketchNode = Annotated[X | Y | ..., Field(discriminator="kind")]
    # ``re.DOTALL`` so the union body across lines is allowed.
    union_re = re.compile(
        r"SketchNode\s*=\s*Annotated\[.*?\bField\s*\(\s*discriminator\s*=\s*[\"']kind[\"']",
        re.DOTALL,
    )
    mashbill_dir = plot_root / "mashbill"
    union_defined_somewhere = False
    try:
        for py in mashbill_dir.glob("*.py"):
            if union_re.search(py.read_text(encoding="utf-8")):
                union_defined_somewhere = True
                break
    except OSError as exc:  # pragma: no cover — repo guarantees presence
        return f"reset_complete_check: cannot scan {mashbill_dir}: {exc}"
    if not union_defined_somewhere:
        failures.append(
            "1) No module under ``mashbill/`` exposes ``SketchNode = "
            "Annotated[Union[...]]`` (the 15-way discriminated union). "
            "Reverting to a god ``SketchNode`` class violates "
            "D-2026-05-12-B Phase 1."
        )

    # 2 & 3) Deleted god files must stay absent.
    god_files = [
        "viewer/src/canvases/SketchInspector.tsx",
        "viewer/src/canvases/SketchNode.tsx",
    ]
    for rel in god_files:
        full = plot_root / rel
        if full.exists():
            failures.append(
                f"2/3) ``{rel}`` was re-created on disk. The v0.15 "
                "reset deleted this god component (Phase 2.10 / 3.5); "
                "per-kind responsibilities live in ``inspectors/{kind}/`` "
                "and ``nodes/{kind}/``."
            )

    # 4) No canvas_kind branching in sketch hooks.
    sketch_dir = plot_root / "viewer" / "src" / "canvases" / "sketch"
    canvas_kind_re = re.compile(
        r"canvas_kind\s*(===|!==|\)|case\s+['\"])",
    )
    if sketch_dir.is_dir():
        for entry in sketch_dir.iterdir():
            if not entry.is_file() or entry.suffix not in {".ts", ".tsx"}:
                continue
            try:
                content = entry.read_text(encoding="utf-8")
            except OSError:
                continue
            # Strip /* ... */ block comments + // line comments.
            stripped = re.sub(r"/\*[\s\S]*?\*/", "", content)
            stripped = "\n".join(
                re.sub(r"//.*$", "", line) for line in stripped.split("\n")
            )
            if canvas_kind_re.search(stripped):
                failures.append(
                    f"4) ``viewer/src/canvases/sketch/{entry.name}`` contains "
                    "a ``canvas_kind`` branching pattern. Per Phase 3.4 the "
                    "sketch transforms never branch on canvas kind; each "
                    "wrapper supplies behaviour via 4 explicit props "
                    "(``hideRootServiceNode`` / ``shouldDrill`` / "
                    "``showFoldButton`` / ``injectAnchor``)."
                )

    if not failures:
        return None

    return (
        "### v0.15 structural reset regression (D-2026-05-12-B → -F)\n\n"
        + "\n".join(f"- {f}" for f in failures)
        + "\n\nThis commit re-introduces a god dispatch the reset was "
        "designed to eliminate. Either revert the offending change or, "
        "if the violation is genuinely the right design call, open a "
        "fresh ``D-YYYY-MM-DD-X`` entry in ``mashbill/docs/DECISIONS.md`` "
        "explaining the reversal and update this gate accordingly."
    )


def cross_cutting_bundle_check(
    staged: list[str], plot_root: Path
) -> str | None:
    """Return a deny message if cross-cutting visual code and feature
    code are both staged in the same commit. Returns None when OK.

    Cross-cutting visual code = CROSS_CUTTING_VISUAL_CODE (currently
    just ``viewer/src/styles.css``). Feature code = any other file
    under ``viewer/`` or ``mashbill/`` (tests excluded — they ship
    with their target). Docs-only commits are never blocked.
    """
    prefix = plot_root.name + "/"
    rel = [p[len(prefix):] for p in staged if p.startswith(prefix)]
    visual = {p for p in rel if p in CROSS_CUTTING_VISUAL_CODE}
    feature = [
        p
        for p in rel
        if (p.startswith("viewer/") or p.startswith("mashbill/"))
        and p not in CROSS_CUTTING_VISUAL_CODE
        and not p.startswith("viewer/tests/")
    ]
    if not (visual and feature):
        return None
    feature_preview = feature[:5] + (["…"] if len(feature) > 5 else [])
    return (
        "### Cross-cutting visual change bundled with feature change\n\n"
        f"- Visual (cross-cutting SSOT): {sorted(visual)}\n"
        f"- Feature: {feature_preview}\n\n"
        "Split this into two atomic commits per D-2026-05-11-C:\n"
        "1. Visual fix only — own D-YYYY-MM-DD-X entry in DECISIONS.md.\n"
        "2. Feature change — depends on (1).\n"
        "\n"
        "Rationale: bundling a cross-cutting visual change with a\n"
        "feature change makes post-hoc causation unreadable (see\n"
        "v0.13.10). The cursor flicker → auto-layout misattribution\n"
        "that drove this gate is documented in D-2026-05-10-G and\n"
        "D-2026-05-11-C.\n"
    )


def run_check(command: list[str], cwd: Path) -> tuple[bool, str]:
    """Run a shell command, return (success, combined_output)."""
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
    except subprocess.TimeoutExpired as exc:
        return False, f"timeout running {' '.join(command)}: {exc}"
    output = (result.stdout or "") + (result.stderr or "")
    return result.returncode == 0, output


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return 0

    tool_name = payload.get("tool_name", "")
    if tool_name != "Bash":
        print(json.dumps({"continue": True}))
        return 0

    command = (payload.get("tool_input") or {}).get("command", "")
    if not GATING_COMMAND_RE.search(command):
        print(json.dumps({"continue": True}))
        return 0

    plot_root = find_plot_root()
    if plot_root is None:
        # Outside a Novel working tree
        print(json.dumps({"continue": True}))
        return 0

    repo_root = plot_root.parent  # noory-ai/
    staged = staged_paths(repo_root)
    if not staged:
        print(json.dumps({"continue": True}))
        return 0

    failures: list[str] = []

    if viewer_changes_staged(staged, plot_root):
        viewer_dir = plot_root / "viewer"
        ok, out = run_check(["npx", "tsc", "--noEmit"], cwd=viewer_dir)
        if not ok:
            failures.append(
                f"### viewer tsc --noEmit failed\n\n```\n{out.strip()[-2000:]}\n```"
            )
        ok, out = run_check(["npx", "vitest", "run"], cwd=viewer_dir)
        if not ok:
            failures.append(
                f"### viewer vitest run failed\n\n```\n{out.strip()[-2000:]}\n```"
            )

    if mcp_changes_staged(staged, plot_root):
        ok, out = run_check(["uv", "run", "pytest"], cwd=plot_root)
        if not ok:
            failures.append(
                f"### mashbill pytest failed\n\n```\n{out.strip()[-2000:]}\n```"
            )

    bundle_msg = cross_cutting_bundle_check(staged, plot_root)
    if bundle_msg:
        failures.append(bundle_msg)

    reset_msg = reset_complete_check(staged, plot_root)
    if reset_msg:
        failures.append(reset_msg)

    if failures:
        message = (
            "**Novel pre-commit gate blocked the commit.**\n\n"
            "Fix the failures below, re-stage, then retry the commit. The gate is "
            "registered in `mashbill/hooks/hooks.json` (PreToolUse on Bash, matcher = "
            "`git commit|push`).\n\n"
            + "\n\n".join(failures)
        )
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": message,
            }
        }
        print(json.dumps(output))
        return 0

    print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
