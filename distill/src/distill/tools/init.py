"""init tool — One-step onboarding: config setup and environment scan."""

from __future__ import annotations

from pathlib import Path

from distill.config import DistillConfig, load_config
from distill.scanner.scanner import scan_environment
from distill.store.scope import detect_project_root, detect_workspace_root
from distill.store.types import KnowledgeScope


def _ensure_config(
    project_root: str, scope: KnowledgeScope, workspace_root: str | None = None
) -> tuple[bool, Path]:
    """Create config.json with defaults if it doesn't exist. Returns (created, path)."""
    import json

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
    """One-step Distill onboarding: create config and scan environment.

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

    lines.append("")

    # Next step guidance
    if config.sources.dirs:
        dir_list = ", ".join(config.sources.dirs)
        lines.append(f"sources.dirs configured: {dir_list}")
        lines.append("Run ingest(path) for each directory to extract knowledge from docs.")
    else:
        lines.append(
            "Distill initialized. Use learn(transcript_path, session_id) "
            "to extract knowledge from conversations,"
        )
        lines.append(
            "or add directories to sources.dirs in config.json "
            "and run ingest(path) to ingest docs."
        )

    return "\n".join(lines)
