"""Helper utilities for MCP tools."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from distill.store.metadata import MetadataStore
from distill.store.scope import detect_project_root, detect_workspace_root
from distill.store.types import KnowledgeScope
from distill.store.vector import VectorStore


@dataclass
class ScopeCallbackContext:
    """Context passed to for_each_scope callback."""

    scope: KnowledgeScope
    meta: MetadataStore
    vector: VectorStore | None = None


async def for_each_scope(
    scope_param: KnowledgeScope | None,
    project_root: str | None,
    callback: Callable[[ScopeCallbackContext], None],
    include_vector: bool = False,
    workspace_root: str | None = None,
) -> None:
    """Iterate over resolved scopes with automatic store lifecycle management.

    3-tier resolution: global → workspace → project (when all roots present).
    Silently skips scopes that don't exist yet.
    """
    if scope_param:
        scopes: list[KnowledgeScope] = [scope_param]
    elif project_root and workspace_root:
        scopes = ["global", "workspace", "project"]
    elif workspace_root:
        scopes = ["global", "workspace"]
    elif project_root:
        scopes = ["global", "project"]
    else:
        scopes = ["global"]

    for scope in scopes:
        ws_root = workspace_root if scope == "workspace" else None
        try:
            with MetadataStore(scope, project_root, ws_root) as meta:
                if include_vector:
                    with VectorStore(scope, project_root, ws_root) as vector:
                        result = callback(ScopeCallbackContext(scope=scope, meta=meta, vector=vector))
                        # Support both sync and async callbacks
                        if hasattr(result, "__await__"):
                            await result  # type: ignore[union-attr]
                else:
                    result = callback(ScopeCallbackContext(scope=scope, meta=meta, vector=None))
                    # Support both sync and async callbacks
                    if hasattr(result, "__await__"):
                        await result  # type: ignore[union-attr]
        except Exception:
            # scope may not exist yet — skip
            pass


def resolve_scope_context(
    scope_param: KnowledgeScope | None,
) -> tuple[list[KnowledgeScope], str | None, str | None]:
    """Resolve scope parameter, project root, and workspace root for tools.

    Returns (scopes, project_root, workspace_root).
    """
    project_root = detect_project_root()
    workspace_root = detect_workspace_root()

    # workspace_root == project_root when CWD is the git root itself
    if workspace_root == project_root:
        workspace_root = None

    if scope_param:
        scopes: list[KnowledgeScope] = [scope_param]
    elif project_root and workspace_root:
        scopes = ["global", "workspace", "project"]
    elif workspace_root:
        scopes = ["global", "workspace"]
    elif project_root:
        scopes = ["global", "project"]
    else:
        scopes = ["global"]

    return scopes, project_root, workspace_root
