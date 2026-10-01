---
name: mashbill-publish-service
user-invocable: true
description: Publish a validated Novel project snapshot and service release in immutable format F.
metadata:
  version: "0.167.1"
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
3. Ask the person which blueprint bump to publish (`major`, `minor`, or
   `patch`) and obtain permission. Pass that bump to
   `publish_project_snapshot_tool` to freeze the shared foundation, actors,
   and entities as the next `vP` snapshot. If the blueprint is unchanged,
   stop and report that no publication was created.
4. Call `publish_service_tool` for the selected service. It validates references
   and publishes the next `vS` release based on the latest `vP`.
   If either publish tool fails and lists nodes that need an English id
   (their names have letters outside ASCII, for example Korean), propose one
   short English id per node that translates its meaning, show the list to the
   person, and call the same tool again with `slugs={node_id: id}` once they
   confirm. Never invent ids the person has not seen.
5. Return both manifest versions and the exact release directory. Blueprint
   publication creates its own commit and tag; create no other tag or commit
   unless the user separately asks for a Git milestone.

Never edit an existing published directory. A changed design produces a new
snapshot or release.
