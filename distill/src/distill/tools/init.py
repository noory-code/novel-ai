"""init tool — One-step onboarding: config setup, environment scan, and docs ingest."""

from __future__ import annotations

import json
from pathlib import Path

from distill.config import DistillConfig, load_config
from distill.scanner.scanner import scan_environment
from distill.store.scope import detect_project_root, detect_workspace_root
from distill.store.types import KnowledgeScope

_SKILL_CONTENTS: dict[str, str] = {
    "distill-init": """\
---
name: distill-init
description: Initialize Distill in the current project — create config, install hooks, scan environment
---

# /distill-init

Call `mcp__distill__init()` to set up Distill in the current project.

## What it does
- Creates `.distill/config.json` (project or workspace scope)
- Installs distill skills into `.claude/`
- Registers hooks in `~/.claude/settings.local.json`
- Scans `.claude/` for existing rules/skills/agents

## Notes
- No API key needed.
- Safe to run multiple times (idempotent).
- If Distill MCP not connected, check `.mcp.json`.
""",

    "distill-recall": """\
---
name: distill-recall
description: Search accumulated Distill knowledge by semantic query
---

# /distill-recall

Call `mcp__distill__recall(query="<query>")` with the user's search terms.

## Usage
/distill-recall <query>

## Example
/distill-recall riverpod state management
→ `mcp__distill__recall(query="riverpod state management")`

## Notes
- No API key needed.
- Searches global + workspace + project scopes automatically.
- Results show type, project tag, scope, confidence, and tags.
""",

    "distill-learn": """\
---
name: distill-learn
description: Extract and store knowledge from a Claude Code conversation transcript
---

# /distill-learn

Call `mcp__distill__learn(transcript_path="<path>", session_id="<id>")`.

## Usage
/distill-learn <transcript_path> <session_id>

## Example
/distill-learn ~/.claude/projects/my-project/abc123.jsonl abc123
→ `mcp__distill__learn(transcript_path="~/.claude/projects/my-project/abc123.jsonl", session_id="abc123")`

## Notes
- Requires `ANTHROPIC_API_KEY` in shell env.
- If no API key: hooks use `claude -p` subprocess automatically.
""",

    "distill-ingest": """\
---
name: distill-ingest
description: Extract and store knowledge from markdown/text files (docs, wiki, notes)
---

# /distill-ingest

Call `mcp__distill__ingest(path="<path>")` to process a directory or file.

## Usage
/distill-ingest <path>

## Example
/distill-ingest docs/
→ `mcp__distill__ingest(path="docs/")`

## Notes
- Requires `ANTHROPIC_API_KEY`.
- Skips unchanged files automatically (content hash check).
- Supported: `.md`, `.txt`, `.rst` files.
""",

    "distill-crystallize": """\
---
name: distill-crystallize
description: Consolidate accumulated knowledge chunks into distill rule/skill/agent files
---

# /distill-crystallize

Call `mcp__distill__memory(action="crystallize")`.

## What it does
- Analyzes all stored knowledge chunks
- Creates or updates `.claude/rules/distill-*.md` rule files
- Optionally creates skills and agents from patterns
- Reports created/updated/removed files

## Notes
- Requires `ANTHROPIC_API_KEY`.
- Run periodically after accumulating 10+ new chunks.
""",

    "distill-profile": """\
---
name: distill-profile
description: Show Distill knowledge statistics — entry counts, types, scopes, top tags
---

# /distill-profile

Call `mcp__distill__profile()`.

## What it shows
- Total knowledge entries per scope (global/workspace/project)
- Breakdown by type (pattern, preference, decision, etc.)
- Top tags
- Last crystallize timestamp

## Notes
- No API key needed.
""",

    "distill-digest": """\
---
name: distill-digest
description: Detect duplicate and stale Distill knowledge entries
---

# /distill-digest

Call `mcp__distill__digest()`.

## What it does
- Finds near-duplicate entries (semantic similarity)
- Identifies stale entries (not accessed recently)
- Reports suggestions for cleanup

## Notes
- No API key needed.
- Use `mcp__distill__memory(action="delete", id="<id>")` to remove entries after reviewing.
""",

    "distill-memory": """\
---
name: distill-memory
description: Manage Distill knowledge entries — promote, demote, delete, or crystallize
---

# /distill-memory

Call `mcp__distill__memory(action="<action>", id="<id>")`.

## Actions

### Promote (project → global)
`mcp__distill__memory(action="promote", id="<entry-id>")`

### Demote (global → project)
`mcp__distill__memory(action="demote", id="<entry-id>")`

### Delete
`mcp__distill__memory(action="delete", id="<entry-id>")`

### Crystallize (generate rules from chunks)
`mcp__distill__memory(action="crystallize")`
Requires `ANTHROPIC_API_KEY`.

## Notes
- Entry IDs are shown in `mcp__distill__profile()` output.
- No API key needed for promote/demote/delete.
""",
}


def _detect_distill_dir() -> Path:
    """Detect the distill repo root by walking up from the package __file__."""
    import distill as _pkg
    # src/distill/__init__.py → src/distill/ → src/ → repo root
    return Path(_pkg.__file__).parent.parent.parent


_HOOK_COMMANDS = {
    "PreCompact": "python -m distill.hooks.distill_hook",
    "SessionEnd": "python -m distill.hooks.distill_hook",
}


def _install_hooks(distill_dir: Path, _settings_path: Path | None = None) -> str:
    """Install distill hooks into ~/.claude/settings.local.json.

    Merges into existing hooks without overwriting unrelated entries.
    Returns a status line for inclusion in init() output.
    """
    settings_path = _settings_path or Path.home() / ".claude" / "settings.local.json"

    # Read existing settings
    try:
        if settings_path.exists():
            settings: dict = json.loads(settings_path.read_text("utf-8"))
            if not isinstance(settings, dict):
                settings = {}
        else:
            settings = {}
    except (json.JSONDecodeError, OSError):
        return "⚠ Could not read settings.local.json — hooks not installed (check file manually)"

    hooks: dict = settings.setdefault("hooks", {})
    installed: list[str] = []
    already: list[str] = []

    for event, module in _HOOK_COMMANDS.items():
        command = f"uv --directory {distill_dir} run {module}"
        entries: list = hooks.setdefault(event, [])
        # Check for duplicate (any entry containing same module path)
        if any(isinstance(e, dict) and module in e.get("command", "") for e in entries):
            already.append(event)
            continue
        entries.append({"type": "command", "command": command})
        installed.append(event)

    # Write back
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False), "utf-8")
    except OSError as err:
        return f"⚠ Could not write settings.local.json: {err}"

    if not installed:
        return f"✓ Hooks already registered ({', '.join(already)}) in {settings_path}"

    msg = f"✓ Hooks installed: {', '.join(installed)} → {settings_path}"
    if already:
        msg += f" ({', '.join(already)} already registered)"
    return msg


def _install_skills(project_root: str) -> list[tuple[bool, str, Path]]:
    """Install all distill skills into .claude/skills/. Returns list of (created, name, path)."""
    results = []
    for name, content in _SKILL_CONTENTS.items():
        skill_path = Path(project_root) / ".claude" / "skills" / name / "SKILL.md"
        if skill_path.exists():
            results.append((False, name, skill_path))
        else:
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(content, encoding="utf-8")
            results.append((True, name, skill_path))
    return results


def _ensure_config(project_root: str, scope: KnowledgeScope, workspace_root: str | None = None) -> tuple[bool, Path]:
    """Create config.json with defaults if it doesn't exist. Returns (created, path)."""
    if scope == "global":
        config_path = Path.home() / ".distill" / "config.json"
    elif scope == "workspace" and workspace_root:
        config_path = Path(workspace_root) / ".distill" / "config.json"
    else:
        config_path = Path(project_root) / ".distill" / "config.json"

    if config_path.exists():
        return False, config_path

    config_path.parent.mkdir(parents=True, exist_ok=True)
    defaults = DistillConfig()
    config_path.write_text(
        json.dumps(defaults.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return True, config_path


def _format_scan_summary(project_root: str) -> str:
    """Scan .claude/ and return a human-readable summary line."""
    env = scan_environment(project_root)
    s = env.summary
    parts = []
    if s.total_rules:
        parts.append(f"{s.total_rules} rules")
    if s.total_skills:
        parts.append(f"{s.total_skills} skills")
    if s.total_agents:
        parts.append(f"{s.total_agents} agents")
    return ", ".join(parts) if parts else "no rules/skills/agents found"


async def init(
    scope: KnowledgeScope | None = None,
    caller_cwd: str | None = None,
    _project_root: str | None = None,
) -> str:
    """One-step Distill onboarding: create config, scan environment, and report configured dirs.

    Args:
        scope: Storage scope — "global", "project", or "workspace" (default: nearest available).
        caller_cwd: Caller's working directory for project root detection.
        _project_root: Override project root (for testing).
    """
    project_root = _project_root or detect_project_root(cwd=caller_cwd)
    workspace_root = detect_workspace_root(cwd=caller_cwd)
    if workspace_root == project_root:
        workspace_root = None

    # Default to nearest available scope
    if scope:
        effective_scope: KnowledgeScope = scope
    elif project_root and workspace_root and project_root != workspace_root:
        # Monorepo subpackage: workspace scope takes priority
        effective_scope = "workspace"
    elif project_root:
        effective_scope = "project"
    elif workspace_root:
        effective_scope = "workspace"
    else:
        effective_scope = "global"

    lines: list[str] = []

    # 1. Ensure config.json exists
    created, config_path = _ensure_config(project_root, effective_scope, workspace_root)
    if created:
        lines.append(f"✓ Config created: {config_path}")
    else:
        lines.append(f"✓ Config already exists: {config_path}")

    # Load config (may have just been created)
    config = load_config(project_root)

    # 2. Scan environment
    scan_summary = _format_scan_summary(project_root)
    lines.append(f"✓ Scanned environment: {scan_summary}")

    # 3. Install distill skills
    if project_root:
        skill_results = _install_skills(project_root)
        created_skills = [name for created, name, _ in skill_results if created]
        existing_skills = [name for created, name, _ in skill_results if not created]
        if created_skills:
            lines.append(f"✓ Skills installed: {', '.join(f'/{n}' for n in created_skills)}")
        if existing_skills:
            lines.append(f"✓ Skills already exist: {', '.join(f'/{n}' for n in existing_skills)}")

    # 4. Install hooks into ~/.claude/settings.local.json
    try:
        hook_line = _install_hooks(_detect_distill_dir())
    except Exception as err:
        hook_line = f"⚠ Hooks not installed: {err}"
    lines.append(hook_line)

    lines.append("")

    # 5. Next step guidance
    if config.sources.dirs:
        dir_list = ", ".join(config.sources.dirs)
        lines.append(f"sources.dirs configured: {dir_list}")
        lines.append("Run ingest(path) for each directory to extract knowledge from docs.")
    else:
        lines.append(
            "Distill initialized. Use learn(transcript_path, session_id) to extract knowledge from conversations,"
        )
        lines.append(
            "or add directories to sources.dirs in config.json and run ingest(path) to ingest docs."
        )

    return "\n".join(lines)
