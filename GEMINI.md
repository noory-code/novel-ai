# Novel AI extension guidance

This extension provides four independent local MCP servers. Use the server that
owns the artifact instead of moving the same information between stores.

| Server | Use it for | Project data |
|---|---|---|
| Mashbill | Service structure, canvases, nodes, relationships, and format-F publication | `.noory/novel/` |
| Solera | Executable work trees, deterministic gates, progress, feedback, and retrospectives | `.noory/solera/` |
| Proof | Immutable decisions and explicit supersession | `.noory/proof/` |
| Distill | Durable knowledge initialization, storage, search, maintenance, and recall | `.noory/distill/`, `~/.distill/` |

Pass the current workspace directory as `project_root` or `project_path` when a
tool requests it. Keep cross-plugin links as stable identifiers or published
files; never invent a Python import between plugins.

For Distill on Gemini CLI, use `init` once, `recall` before relevant work, and
`store` when the current model has already extracted reusable knowledge. The
extension intentionally does not expose Distill's `learn`, `ingest`, or
`crystallize` paths because those require server-initiated MCP Sampling, which
Gemini CLI does not currently document as a client capability.

Solera gate completion executes the exact command stored in the current leaf.
Show that command to the user before the first execution in a project. Re-pin
is a two-step human-controlled operation: call `propose_spec_repin`, present
the result, and call `apply_spec_repin` only after explicit approval.
