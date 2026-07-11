---
name: mashbill-new-project
user-invocable: true
description: Create a structured Novel design project in a user-selected workspace directory.
metadata:
  version: "0.167.1"
  category: action
  type: unit
  style: procedure
  triggers: [mashbill new project, novel new project, create a service blueprint]
  uses: [create_project_tool, discover_workspace_projects]
---

# Create a Mashbill project

Create one project under `{project_path}/.noory/novel/{project_id}/`. The data
directory belongs next to the code it describes.

## Procedure

1. Resolve `project_path` from the directory named by the user or the current
   workspace. If the intended directory is ambiguous, call
   `discover_workspace_projects` and ask the user to choose. Never invent a
   subdirectory.
2. Obtain a non-empty display name from the user.
3. Derive a stable lowercase kebab-case `project_id`. Add a short suffix only
   when the base id already exists.
4. Call `create_project_tool(project_path, project_id, name)`. It seeds the
   Foundation, Actors, and Services canvases.
5. Report the exact resulting directory and the project id. Do not call
   `open_canvas` unless the user says a compatible Novel UI is already running.

If creation reports that the id exists, show the existing project and ask
whether to use it or allocate a new id. Deletion requires an explicit user
request because `delete_project_tool` removes the entire project directory.
