---
name: mashbill-new-project
user-invocable: true
description: Create a new Novel project (blueprint) in a chosen directory and open it. Asks WHERE to create it — built for monorepos where several app services (e.g. Banas + Banana) are designed side by side, each with its own .plot/ next to its code.
metadata:
  version: "0.1.0"
  category: action
  type: unit
  style: action
  triggers: [plot new project, new plot project, 새 플롯 프로젝트, 플롯 프로젝트 만들어, create plot project, plot create project, 프로젝트 만들어줘, make a plot project, 설계도 만들어]
  uses: [create_project_tool, discover_workspace_projects, open_canvas]
---

# /mashbill-new-project

Create a fresh Novel **project** (a blueprint: Foundation + Actors + Services
canvases) under `{target_dir}/.plot/{project_id}/` and open the viewer on it.

A Novel project's `.plot/` lives **next to the code it describes**, not at the
monorepo root. The plugin is installed once at the monorepo root, but each app
service gets its own `.plot/` in its own subdirectory. Example: building
**Banas** and **Banana** at once →
`monorepo/banas/.plot/{id}/` and `monorepo/banana/.plot/{id}/`.

This skill exists because creation needs a deliberate **WHERE** answer — the
viewer's "+ Add a Project" picker does the same job from the UI.

## When to run

The user says "new project", "make me a Novel project", "바나나 프로젝트
만들어줘", "설계도 만들어" — or starts designing a service that does not yet
have a `.plot/` project.

## Steps

`if` the user did not name a target directory `then` resolve the **workspace
root** (the monorepo): use the directory the user named, else the current
working directory.

1. **Pick the target directory** (where `.plot/` will be created):
   - `if` the user named a subdirectory (e.g. "banana", "in apps/admin")
     `then` use `{workspace_root}/{that subdir}` as `target_dir`.
   - `else` call `discover_workspace_projects(workspace_root)` to show which
     subdirectories already hold a project, then ask the user which directory
     the new project belongs in. Offer the workspace root itself as one option.
   - **Never** invent a subdirectory. If the named one does not exist, ask the
     user to confirm or create it first.
2. **Name it.** `if` the user gave a name `then` use it; `else` ask for a short
   name (e.g. "Banana"). There is no silent default — do not proceed without a
   name.
3. **Build the id.** `project_id` = kebab-cased name + a short suffix to keep it
   unique (e.g. `banana-7f3a`). Lower-case, ASCII, hyphen-separated.
4. **Create.** Call
   `create_project_tool(project_path=target_dir, project_id=project_id, name=name)`.
   This creates `{target_dir}/.plot/{project_id}/` seeded with Foundation,
   Actors, and Services canvases.
5. **Open.** Call `open_canvas(project_path=target_dir, project_id=project_id)`
   to open the viewer on the new project.
6. Tell the user the on-disk location (`{target_dir}/.plot/{project_id}/`) so
   they know where the blueprint lives relative to their code.

## Errors

- **`project already exists`** (409): the `project_id` is taken in that
  `.plot/`. Append a different suffix and retry, or open the existing one.
- **`project_path does not exist`** (404): the chosen `target_dir` is not a
  real directory. Confirm the path with the user.

## Inverse

There is no "un-create". Use `delete_project_tool(project_path, project_id)`
if the user changes their mind (it removes `{target_dir}/.plot/{project_id}/`).
