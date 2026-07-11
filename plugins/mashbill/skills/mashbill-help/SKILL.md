---
name: mashbill-help
user-invocable: true
description: Explain Mashbill's headless Novel design model, data layout, MCP tools, and workflows.
metadata:
  version: "0.167.1"
  category: meta
  type: unit
  style: guide
  triggers: [mashbill help, novel design help, how to use mashbill, structure this service]
  uses: [mashbill-new-project, mashbill-read-project, mashbill-publish-service]
---

# Mashbill

Mashbill is Novel's headless structured-design engine. It stores a project's
foundation, actors, services, features, entities, and relationships under
`.noory/novel/` and exposes them as MCP tools.

## Core workflows

| Skill | Outcome |
|---|---|
| `mashbill-new-project` | Create a structured design project in a chosen workspace |
| `mashbill-read-project` | Read the current project and summarize its design state |
| `mashbill-publish-service` | Validate and publish immutable format-F snapshots |

## MCP tool groups

- Project discovery: `list_projects`, `discover_workspace_projects`, `get_project`
- Project mutation: `create_project_tool`, `rename_project`, `delete_project_tool`
- Canvas access: `get_canvas`, `update_canvas`, `list_detail_canvases`
- Narrow graph mutation: `create_node`, `update_node`, `create_edge`,
  `set_node_references`
- Search and principles: `search_project_nodes`, `get_design_principles`
- Publication: `publish_project_snapshot_tool`, `publish_service_tool`
- Milestones: `tag_project`, `list_project_tags`, `delete_project_tag`

Pass the current workspace as `project_path`. Prefer `update_node` for one node;
`update_canvas` intentionally replaces a complete canvas. The plugin is
headless and does not require or bundle the commercial Novel UI.
