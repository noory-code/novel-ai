---
name: mashbill-publish-service
user-invocable: true
description: Publish a validated Novel project snapshot and service release in immutable format F.
metadata:
  version: "0.167.0"
  category: publication
  type: unit
  style: procedure
  triggers: [publish novel service, publish format f, release service design]
  uses: [get_project, publish_project_snapshot_tool, publish_service_tool]
---

# Publish a Mashbill service

Publishing is explicit. It creates immutable format-F data that another tool,
including Solera, can import by value.

## Procedure

1. Resolve `project_path`, `project_id`, and `service_id` from the user's
   request. If any identifier is ambiguous, call `get_project` and ask the user
   to choose from the actual stored ids.
2. Read the project and service design. Report missing required structure before
   attempting publication.
3. Call `publish_project_snapshot_tool` to freeze the shared foundation,
   actors, and entities as the next `vP` snapshot.
4. Call `publish_service_tool` for the selected service. It validates references
   and publishes the next `vS` release based on the latest `vP`.
5. Return both manifest versions and the exact release directory. Do not tag or
   commit the repository unless the user separately asks for a Git milestone.

Never edit an existing published directory. A changed design produces a new
snapshot or release.
