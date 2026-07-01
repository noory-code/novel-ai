"""Legacy-sketch migration facade (D-2026-06-11-B).

The 916-line god module was split along its own section headers into
focused modules; this file re-exports the two public entry points so no
import site (endpoints_projects.py, canvas_io.py, mcp_tools.py, tests)
changes:

    migrate_v01_models.py — legacy v0.1 ``_V01SketchDoc`` + ``_V01SketchNode``
                            Pydantic models, plus ``_normalise_legacy_node_kinds``
    migrate_builders.py   — per-canvas builders that convert legacy nodes
                            into current per-kind classes
    migrate_v01.py        — top-level v0.1 → v0.2 migration loop
                            (``migrate_v01_to_v02``)
    migrate_foundation.py — inline Foundation-canvas schema upgrade
                            (``upgrade_foundation_canvas_if_needed``)

Algorithm
---------

For every ``.plot/sketches/{id}.json`` that looks like a v0.1 SketchDoc:

    1. Normalise legacy node kinds (see ``_normalise_legacy_node_kinds``) then
       parse as ``_V01SketchDoc``.
    2. Create ``.plot/sketches/{id}/`` and the four v0.4 canvas files:
       - ``project.json``
       - ``core.json``  (project anchor + mission + core-value + identity)
       - ``actors.json`` (actor subtree, parent chain cleaned)
       - ``services/canvas.json`` (top-level services, no nesting)
       - ``services/{service_id}/detail.json`` per top-level service
    3. Rename the original to ``{id}.json.v01.bak``.

Running a second time does nothing (idempotent). Malformed v0.1 files are
left in place so the user can fix them by hand.

v0.5 Core schema upgrade (inline on open)
-----------------------------------------

``upgrade_core_canvas_if_needed`` handles Core canvases that were written
under earlier schemas (``core`` octagon anchor, ``identity_facet`` child
nodes). It rewrites the raw dict before Pydantic validation and, when
changes were made, persists the result so subsequent loads are cheap.
"""

from __future__ import annotations

from mashbill.migrate_foundation import (
    upgrade_foundation_canvas_if_needed as upgrade_foundation_canvas_if_needed,
)
from mashbill.migrate_v01 import (
    migrate_v01_to_v02 as migrate_v01_to_v02,
)

# Backwards-compatible alias for any in-process caller still importing the
# pre-v0.10 name. New code uses ``upgrade_foundation_canvas_if_needed``.
upgrade_core_canvas_if_needed = upgrade_foundation_canvas_if_needed
