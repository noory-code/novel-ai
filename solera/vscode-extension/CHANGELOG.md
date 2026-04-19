# Changelog

## [4.0.0] — 2026-04-19

Initial Marketplace release. Ships as part of unified Solera v4.0.0 — same version as the Claude Code plugin, same `.solera/` data format, same MCP server (bundled here via `../viewer/dist/` and `../solera_mcp/` from the parent plugin directory).

### Added

- Command **Solera: Open Canvas** launches the viewer in a VSCode webview panel.
- Spawns `uv run python -m solera_mcp` against the current workspace folder, reusing an existing server when one is already healthy on the configured port.
- Detects `.solera/` (Solera v4) or `workspace/` (Solera v3, with a deprecation info notification suggesting `/solera-migrate-workspace-to-dotsolera` in Claude Code).
- Onboarding panel for non-Solera workspaces with prerequisite + install instructions.
- All four canvases (Service / Plan / Build / Live) render via the bundled `media/viewer/` (copied from `../viewer/dist/` by the `vscode:prepublish` hook).
- Server lifecycle: SIGTERM with 5s grace period, then SIGKILL on extension deactivation. Premature child exit detected within 200ms (was 15s — fixed during v4.0 development).
- Per-load CSP nonce; `connect-src` opens `http://127.0.0.1:{port}` and `ws://127.0.0.1:{port}` only.

### Prerequisites

- VSCode 1.85+.
- Python 3.11+ and `uv` (https://docs.astral.sh/uv/) on PATH.
- The `solera-mcp` Python package resolvable to `uv` (installed via the Solera Claude Code plugin marketplace).

### Naming

The package on VSCode Marketplace is `noory-code.solera`. Previous internal naming (`solera-map-vscode`, `noory-code.solera-map`) was used during development and never published.

### Notes

- VSCode Marketplace policy bans extensions that download executables — this extension cannot install `uv` for you. If `uv` is missing, the spawn fails with a clear "Open Output" notification.
- No telemetry. Privacy-first per [Solera's PRIVACY.md](https://github.com/noory-code/noory-ai/blob/main/solera/PRIVACY.md).
