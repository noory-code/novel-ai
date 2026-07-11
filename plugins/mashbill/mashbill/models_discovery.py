"""Workspace discovery + directory-tree picker response models
(v0.32.0, D-2026-05-31-L). Extracted from the models.py god module
(D-2026-06-11-B).

A monorepo (the workspace root) can hold many Novel projects, each in its own
subdirectory with its own ``.plot/``. These response models back the two new
read-only endpoints: recursive discovery (unified sidebar list) and the
nested directory tree (new-project picker). They are NOT node-kind classes,
so they sit outside the 15-kind schema-parity harness; their TS mirrors are
guarded by the viewer's vitest + tsc.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from mashbill.models_canvas import ProjectDoc


class DiscoveredProject(BaseModel):
    """A project found during workspace discovery, with its directory relative
    to the workspace root (``"."`` for a root-level project)."""

    project: ProjectDoc
    dir: str


class WorkspaceDiscoveryResponse(BaseModel):
    projects: list[DiscoveredProject] = Field(default_factory=list)
    migrated: list[str] = Field(default_factory=list)


class DirTreeNode(BaseModel):
    """A directory in the workspace tree picker. ``rel`` is POSIX-relative to
    the workspace root (``"."`` for the root); ``has_plot`` flags an existing
    ``.plot/`` (i.e. the directory already holds Novel project(s))."""

    name: str
    rel: str
    has_plot: bool = False
    children: list[DirTreeNode] = Field(default_factory=list)


class DirTreeResponse(BaseModel):
    root: DirTreeNode


DirTreeNode.model_rebuild()
