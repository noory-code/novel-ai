---
name: mashbill-new-sketch
user-invocable: true
description: Create a new empty Novel sketch in the current project and open it in the browser.
metadata:
  version: "0.1.0"
  category: action
  type: unit
  style: action
  triggers: [plot new, plot new sketch, plot create, new plot sketch, create plot sketch]
  uses: []
---

# /mashbill-new-sketch

Create a fresh, empty Novel sketch under `{project}/.plot/sketches/` and open the viewer focused on it.

## When to run

The user says "new sketch", "plot new", "make me a new plot" — or at the start of a new design exploration that should not reuse the current sketch.

## Steps

1. Determine the project path:
   - If the user provided one in the message, use that.
   - Otherwise, use the current working directory.
2. Ask the user for a short name if it isn't already given (e.g., "BANAS actors and services v1"). Default to `"Untitled"` if the user declines.
3. Call the MCP tool `create_sketch_tool(project_path, sketch_id, name)` where `sketch_id` is the kebab-cased name plus a short timestamp suffix (e.g., `banas-actors-services-v1-a1b2`).
4. Call `open_canvas(project_path, sketch_id)` to open the viewer at the new sketch.

## Errors

- **`sketch already exists`** (409): pick a different id or append a timestamp.
- **`project_path does not exist`**: ask the user to confirm the path.

## Inverse

There is no "un-create" — use `delete_sketch_tool` if the user changes their mind.
