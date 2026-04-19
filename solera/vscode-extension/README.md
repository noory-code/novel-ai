# Solera (VSCode extension)

Mindmap-style visual layer for [Solera](https://github.com/noory-code/noory-ai) projects, embedded in a VSCode webview. Four canvases over the same `.solera/` data:

- **Service** — Personas, Journeys, Narratives. Upstream of Plan.
- **Plan** — Concept hierarchy as a bilateral mindmap.
- **Build** — radial WBS view (currently same as Plan with build styling).
- **Live** — accumulated value view (currently same as Plan with live styling).

## Prerequisites

- **VSCode 1.85+**.
- **Python 3.11+** with [`uv`](https://docs.astral.sh/uv/) on PATH. The extension cannot install `uv` for you — VSCode Marketplace policy bans extensions that download executables.
- The **`solera-mcp` Python package** resolvable to `uv` (installed via the Solera Claude Code plugin marketplace, or `uv pip install solera-mcp` once the package is on PyPI).
- A folder containing a Solera v4 `.solera/` directory (or v3 `workspace/` — supported with a deprecation warning).

## Usage

1. Open a folder containing a Solera project in VSCode.
2. Run **Solera: Open Canvas** from the Command Palette (`Cmd/Ctrl+Shift+P`).
3. The extension spawns the local server (or reuses one already running on the configured port) and opens the viewer in a webview tab.

If the workspace has no `.solera/` (or `workspace/`), an onboarding panel appears with setup instructions.

## Configuration

| Setting | Default | Purpose |
|---|---|---|
| `solera.command` | `uv run python -m solera_mcp` | Shell command that launches the server in the workspace folder. |
| `solera.port` | `5170` | Local HTTP port the server binds to and the webview talks to. |

## Security model

The webview talks to `http://127.0.0.1:{port}` over an explicit `connect-src` Content-Security-Policy entry. **Localhost is the trust boundary** — the same one the standalone solera-mcp server already uses. Webview scripts run with a per-load nonce; only Vite-emitted bundles execute. No telemetry is sent by this extension.

## Server lifecycle

- Activation is lazy: the extension wakes up only when the `Solera: Open` command is invoked.
- Before spawning, the extension probes `GET /api/health` on the configured port. If a server is already running (e.g. from Claude Code's MCP invocation), it is reused.
- The spawned server runs with `SOLERA_MAP_NO_MCP=1` so it skips the MCP stdio task that would otherwise leak a stdio reader with no client.
- On extension shutdown, the spawned process gets `SIGTERM`; after a 5s grace period, `SIGKILL`.

## Backward compatibility (v3 `workspace/`)

Solera v4.x reads from both `.solera/` (v4) and `workspace/` (v3) for one minor version. If the extension detects only `workspace/`, it shows an info notification suggesting `/solera-migrate-workspace-to-dotsolera` in Claude Code. Solera will drop the v3 fallback in a future minor.

## Tests

Two test suites. Run from `solera/vscode-extension/`:

```bash
npm run test             # unit tests (vitest, 37 tests) — csp / workspaceCheck / ServerProcess
npm run test:integration # integration tests (@vscode/test-electron + mocha) — real VSCode host
```

The integration suite downloads VSCode once (~120 MB, cached under `.vscode-test/`) and launches a clean Extension Host to verify: activation, command registration, default configuration values, and onboarding-webview display for non-Solera folders.

**Known local-macOS limitation (macOS 15 Sequoia+):** Apple's Gatekeeper blocks the test-electron-downloaded VSCode on first launch. Symptoms: `Exit code: 1` with no VSCode output. Workarounds:

1. Open the downloaded app once manually: `open "solera/vscode-extension/.vscode-test/vscode-darwin-arm64-1.85.0/Visual Studio Code.app"` — approve in **System Settings → Privacy & Security → "Open Anyway"** when prompted. Subsequent `npm run test:integration` runs work.
2. Or run on Linux / CI — the issue does not occur there.

Unit tests (`npm run test`) run unchanged on all platforms.

## Building from source

```bash
cd solera/vscode-extension
npm install
npm run vscode:prepublish   # copies viewer/dist into media/viewer + tsc
npx vsce package            # produces solera-{version}.vsix
code --install-extension solera-4.0.0.vsix --force
```

The `vscode:prepublish` script copies `../viewer/dist/` into `media/viewer/`. Re-run it whenever you rebuild the viewer with `cd ../viewer && npm run build`.

## License

MIT — see [LICENSE](LICENSE).
