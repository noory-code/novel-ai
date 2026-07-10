# Novel — next-session queue

The SessionStart hook reads this file at the beginning of each Mashbill session. Public releases do not ship
maintainer-specific tasks, machine paths, or private-workspace links.

## Active queue

No public task is queued.

Repository maintainers may add a public queue item as a level-three heading containing a backtick-wrapped
trigger phrase, an em dash, and a short task title. The hook's parser contract is pinned by its unit tests.

The item must be self-contained in this repository and safe for every plugin user to see. Remove it when the task
is complete; permanent history belongs in `DECISIONS.md` and `CHANGELOG.md`.

## Completed

Historical private-workspace queue entries were removed during the `novel-ai` public-repository migration on
2026-07-10. Their project-management history remains in the private workspace and Git history.
