"""Starlette HTTP handler facade for the v0.4 project / canvas / tag /
publish / files surface (D-2026-06-11-B).

The 965-line god module was split along its own section headers into
focused per-area modules; this file re-exports every endpoint name so no
import site (http_app.py, tests) changes:

    endpoints_common.py     — shared helpers (`_require_plot_root`,
                              `_ApiError`, `_parse_canvas_kind`) + health
    endpoints_projects.py   — projects list/post/get/patch/delete +
                              anchor patch + workspace discover / dir tree /
                              dir create
    endpoints_canvases.py   — canvas get + put (with response decoration:
                              `_md_warnings` + per-node `_dirty`)
    endpoints_tags.py       — tags list/post/delete + read-only at-tag
                              project snapshot
    endpoints_publish.py    — project blueprint publish + per-node publish /
                              unpublish / published-list
    endpoints_files.py      — file get/raw/put + folder post (Inspector MD
                              editor backend, project-scoped)

The legacy v0.1 ``/api/sketches/*`` endpoints have been removed — new
callers use the project/canvas shape directly. ``mashbill/sketches.py``
now only serves the in-process migration script.

`tests/test_module_size.py` pins every endpoint module (and this facade)
under the monorepo 500-line rule.
"""

from __future__ import annotations

from mashbill.endpoints_canvases import (
    canvas_get_endpoint as canvas_get_endpoint,
)
from mashbill.endpoints_canvases import (
    canvas_put_endpoint as canvas_put_endpoint,
)
from mashbill.endpoints_canvases import (
    entity_usage_endpoint as entity_usage_endpoint,
)
from mashbill.endpoints_canvases import (
    master_create_endpoint as master_create_endpoint,
)
from mashbill.endpoints_common import (
    health_endpoint as health_endpoint,
)
from mashbill.endpoints_files import (
    file_get_endpoint as file_get_endpoint,
)
from mashbill.endpoints_files import (
    file_put_endpoint as file_put_endpoint,
)
from mashbill.endpoints_files import (
    file_raw_endpoint as file_raw_endpoint,
)
from mashbill.endpoints_files import (
    folder_post_endpoint as folder_post_endpoint,
)
from mashbill.endpoints_projects import (
    dir_create_endpoint as dir_create_endpoint,
)
from mashbill.endpoints_projects import (
    dir_tree_endpoint as dir_tree_endpoint,
)
from mashbill.endpoints_projects import (
    project_anchor_patch_endpoint as project_anchor_patch_endpoint,
)
from mashbill.endpoints_projects import (
    project_delete_endpoint as project_delete_endpoint,
)
from mashbill.endpoints_projects import (
    project_get_endpoint as project_get_endpoint,
)
from mashbill.endpoints_projects import (
    project_patch_endpoint as project_patch_endpoint,
)
from mashbill.endpoints_projects import (
    project_post_endpoint as project_post_endpoint,
)
from mashbill.endpoints_projects import (
    projects_list_endpoint as projects_list_endpoint,
)
from mashbill.endpoints_projects import (
    workspace_discover_endpoint as workspace_discover_endpoint,
)
from mashbill.endpoints_projects import (
    workspace_git_init_endpoint as workspace_git_init_endpoint,
)
from mashbill.endpoints_publish import (
    format_f_service_publish_endpoint as format_f_service_publish_endpoint,
)
from mashbill.endpoints_publish import (
    format_f_snapshot_endpoint as format_f_snapshot_endpoint,
)
from mashbill.endpoints_publish import (
    project_publish_endpoint as project_publish_endpoint,
)
from mashbill.endpoints_tags import (
    project_at_tag_endpoint as project_at_tag_endpoint,
)
from mashbill.endpoints_tags import (
    tag_delete_endpoint as tag_delete_endpoint,
)
from mashbill.endpoints_tags import (
    tag_post_endpoint as tag_post_endpoint,
)
from mashbill.endpoints_tags import (
    tags_list_endpoint as tags_list_endpoint,
)
