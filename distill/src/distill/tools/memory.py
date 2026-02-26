"""memory tool — Manage knowledge: promote/demote scope, delete entries, crystallize."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from distill.config import load_config
from distill.extractor.crystallize import crystallize
from distill.store.metadata import MetadataStore
from distill.store.scope import detect_project_root, detect_workspace_root
from distill.store.types import KnowledgeChunk
from distill.store.vector import VectorStore
from distill.tools.helpers import for_each_scope

MemoryAction = Literal["promote", "demote", "delete", "crystallize"]

SCOPE_ORDER = ["project", "workspace", "global"]


def _next_scope(current: str, direction: str) -> str | None:
    """Return adjacent scope in the given direction, or None if at boundary."""
    if current not in SCOPE_ORDER:
        return None
    idx = SCOPE_ORDER.index(current)
    if direction == "promote":
        return SCOPE_ORDER[idx + 1] if idx < len(SCOPE_ORDER) - 1 else None
    else:  # demote
        return SCOPE_ORDER[idx - 1] if idx > 0 else None


async def memory(
    action: MemoryAction,
    ctx=None,
    id: str | None = None,
    caller_cwd: str | None = None,
) -> str:
    """Manage knowledge: promote/demote scope, delete entries, or crystallize rules."""
    project_root = detect_project_root(cwd=caller_cwd)
    workspace_root = detect_workspace_root(cwd=caller_cwd)
    if workspace_root == project_root:
        workspace_root = None

    if action == "crystallize":
        return await _handle_crystallize(ctx, project_root, workspace_root)

    if not id:
        return f'Action "{action}" requires an id parameter.'

    if action == "delete":
        return _handle_delete(id, project_root, workspace_root)

    return _handle_promote_demote(action, id, project_root, workspace_root)


async def _handle_crystallize(
    ctx, project_root: str | None, workspace_root: str | None
) -> str:
    """Collect all knowledge and crystallize into rules."""
    try:
        config = load_config(project_root)

        all_chunks: list[KnowledgeChunk] = []
        await for_each_scope(
            None,
            project_root,
            lambda c: all_chunks.extend(c.meta.get_all()),
            workspace_root=workspace_root,
        )

        if not all_chunks:
            return "No knowledge chunks to crystallize."

        report = await crystallize(
            ctx=ctx,
            chunks=all_chunks,
            model=config.crystallize_model,
            project_root=project_root,
        )

        try:
            with MetadataStore("global") as global_meta:
                global_meta.set_meta("last_crystallize", datetime.now(UTC).isoformat())
        except Exception:
            pass

        lines = [f"Crystallized {len(all_chunks)} knowledge chunks."]
        if report.created:
            lines.append(f"Created: {', '.join(report.created)}")
        if report.updated:
            lines.append(f"Updated: {', '.join(report.updated)}")
        if report.removed:
            lines.append(f"Removed: {', '.join(report.removed)}")
        if report.downgraded:
            lines.append(f"Downgraded: {', '.join(report.downgraded)}")
        if report.skills_created:
            lines.append(f"Skills created: {', '.join(report.skills_created)}")
        if report.user_conflicts:
            lines.append("")
            lines.append("⚠ User rule conflicts:")
            for c in report.user_conflicts:
                lines.append(
                    f"  - {c.user_rule_file}: {c.conflicting_content} "
                    f"→ {c.suggestion}"
                )
        lines.append(f"Total rules: {report.total_rules}")

        return "\n".join(lines)
    except Exception as err:
        return f"Error during crystallize: {err}"


def _handle_delete(id: str, project_root: str | None, workspace_root: str | None) -> str:
    """Delete a knowledge entry from any scope (searches all 3 tiers)."""
    for scope in ("global", "workspace", "project"):
        if scope == "workspace" and not workspace_root:
            continue
        if scope == "project" and not project_root:
            continue
        ws_root = workspace_root if scope == "workspace" else None
        try:
            with (
                MetadataStore(scope, project_root, ws_root) as meta,  # type: ignore[arg-type]
                VectorStore(scope, project_root, ws_root) as vector,  # type: ignore[arg-type]
            ):
                if meta.delete(id):
                    vector.remove(id)
                    return f"Deleted knowledge entry {id} from {scope} scope."
        except Exception:
            continue

    return f"Knowledge entry {id} not found."


def _handle_promote_demote(
    action: Literal["promote", "demote"],
    id: str,
    project_root: str | None,
    workspace_root: str | None,
) -> str:
    """Move a knowledge entry one step up (promote) or down (demote) in scope tier."""
    # Find chunk in any scope
    chunk = None
    found_scope: str | None = None

    for scope in SCOPE_ORDER:
        if scope == "workspace" and not workspace_root:
            continue
        if scope == "project" and not project_root:
            continue
        ws_root = workspace_root if scope == "workspace" else None
        try:
            with MetadataStore(scope, project_root, ws_root) as meta:  # type: ignore[arg-type]
                chunk = meta.get_by_id(id)
                if chunk:
                    found_scope = scope
                    break
        except Exception:
            continue

    if not chunk or not found_scope:
        return f"Knowledge entry {id} not found in any scope."

    to_scope = _next_scope(found_scope, action)
    if not to_scope:
        boundary = "global" if action == "promote" else "project"
        return (
            f"Cannot {action}: entry is already at {found_scope} scope "
            f"(boundary: {boundary})."
        )

    if to_scope == "workspace" and not workspace_root:
        return (
            f"Cannot {action} to workspace scope: "
            "no workspace (git) root detected."
        )
    if to_scope == "project" and not project_root:
        return f"Cannot {action} to project scope: no project root detected."

    from_ws_root = workspace_root if found_scope == "workspace" else None
    to_ws_root = workspace_root if to_scope == "workspace" else None

    try:
        with (
            MetadataStore(
                found_scope, project_root, from_ws_root
            ) as from_meta,  # type: ignore[arg-type]
            VectorStore(
                found_scope, project_root, from_ws_root
            ) as from_vector,  # type: ignore[arg-type]
            MetadataStore(
                to_scope, project_root, to_ws_root
            ) as to_meta,  # type: ignore[arg-type]
            VectorStore(
                to_scope, project_root, to_ws_root
            ) as to_vector,  # type: ignore[arg-type]
        ):
            from_meta.move(chunk, to_meta)
            to_vector.index(chunk.id, chunk.content, chunk.tags)
            from_vector.remove(chunk.id)

            event_type = "promoted" if action == "promote" else "demoted"
            to_meta.add_lifecycle_event(
                chunk.id,
                event_type,  # type: ignore[arg-type]
                from_scope=found_scope,  # type: ignore[arg-type]
                to_scope=to_scope,  # type: ignore[arg-type]
            )

            action_word = "Promoted" if action == "promote" else "Demoted"
            return (
                f"{action_word} knowledge entry.\n"
                f"{found_scope} → {to_scope}\n"
                f"ID: {chunk.id}\n"
                f"Content: {chunk.content[:100]}..."
            )
    except Exception as err:
        return f"Error during {action}: {err}"
