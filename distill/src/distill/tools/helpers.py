"""Helper utilities for MCP tools."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from distill.store.metadata import MetadataStore
from distill.store.scope import detect_project_root, detect_workspace_root
from distill.store.types import KnowledgeScope
from distill.store.vector import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class ScopeContext:
    """스코프 해석에 필요한 컨텍스트."""

    global_dir: str
    workspace_dir: str | None
    project_dir: str | None


def _iter_scope_dirs(
    project_root: str | None, workspace_root: str | None
) -> list[tuple[KnowledgeScope, str | None, str | None]]:
    """해석 순서대로 (scope, project_root, workspace_root) 튜플 리스트 반환.

    전역 → 워크스페이스 → 프로젝트 순서로 반환.

    Args:
        project_root: 프로젝트 루트 경로 또는 None
        workspace_root: 워크스페이스 루트 경로 또는 None

    Returns:
        (scope, project_root, workspace_root) 튜플 리스트
    """
    result: list[tuple[KnowledgeScope, str | None, str | None]] = [("global", None, None)]

    if workspace_root and not project_root:
        result.append(("workspace", None, workspace_root))
    elif project_root and not workspace_root:
        result.append(("project", project_root, None))
    elif project_root and workspace_root:
        result.append(("workspace", None, workspace_root))
        result.append(("project", project_root, workspace_root))

    return result


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
        scope_items = [(scope_param, project_root, workspace_root)]
    else:
        scope_items = _iter_scope_dirs(project_root, workspace_root)

    for scope, proj_root, ws_root in scope_items:
        try:
            with MetadataStore(scope, proj_root, ws_root) as meta:
                if include_vector:
                    with VectorStore(scope, proj_root, ws_root) as vector:
                        ctx = ScopeCallbackContext(scope=scope, meta=meta, vector=vector)
                        result = callback(ctx)
                        if hasattr(result, "__await__"):
                            await result  # type: ignore[union-attr]
                else:
                    ctx = ScopeCallbackContext(scope=scope, meta=meta, vector=None)
                    result = callback(ctx)
                    if hasattr(result, "__await__"):
                        await result  # type: ignore[union-attr]
        except Exception:
            logger.debug("Skipping item due to error", exc_info=True)


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
    else:
        scope_items = _iter_scope_dirs(project_root, workspace_root)
        scopes = [scope for scope, _, _ in scope_items]

    return scopes, project_root, workspace_root
