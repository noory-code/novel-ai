---
name: mashbill-read-project
user-invocable: true
description: Read a Novel design project and summarize its foundation, actors, services, features, and gaps.
metadata:
  version: "0.167.1"
  category: analysis
  type: unit
  style: procedure
  triggers: [read novel project, summarize service design, inspect mashbill project]
  uses: [list_projects, get_project, get_canvas, list_detail_canvases]
---

# Read a Mashbill project

## Procedure

1. Use the current workspace as `project_path` unless the user names another.
2. Call `list_projects`. If more than one project exists and the user did not
   identify one, present the ids and ask which project to read.
3. Call `get_project`, then read the `foundation`, `actors`, `services`, and
   `entities` canvases with `get_canvas`.
4. Call `list_detail_canvases` and read each returned feature canvas by passing
   its service id to `get_canvas(canvas_kind="feature")`.
5. Summarize facts from the stored design before offering interpretation:
   foundation, actor responsibilities, service boundaries, feature flows,
   entities, and unresolved or disconnected relationships.

This skill is read-only. Do not call a mutation tool unless the user separately
asks to change the design.
