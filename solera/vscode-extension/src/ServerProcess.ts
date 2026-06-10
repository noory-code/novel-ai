import { spawn, type ChildProcess } from "node:child_process";
import * as vscode from "vscode";

export interface ServerStartOptions {
  /** Shell command, may include args (e.g. `uv run python -m solera_mcp`). */
  command: string;
  /** Working directory — the project folder hosting `.noory/solera/`
   *  (preferred), a legacy `.solera/`, or `workspace/` (v3 fallback). */
  cwd: string;
  /** TCP port the server should bind to. Set via `SOLERA_MAP_PORT`. */
  port: number;
}

const HEALTH_TIMEOUT_MS = 15_000;
const HEALTH_POLL_MS = 200;
const STOP_GRACE_MS = 5_000;

/**
 * Owns the spawned Solera MCP server's lifecycle. The extension uses only
 * the HTTP+WebSocket interface, so the process is started with
 * `SOLERA_MAP_NO_MCP=1` to skip the MCP stdio task that would otherwise leak
 * a stdio reader with no client. Health is verified by polling
 * `GET /api/health` until 200 or timeout.
 *
 * Cross-platform shutdown: SIGTERM on Unix; child.kill('SIGTERM') triggers
 * termination on Windows too (Node maps it to `taskkill /pid /t /f` for
 * non-Unix). A 5s grace, then SIGKILL.
 */
export class ServerProcess {
  private child?: ChildProcess;
  private currentPort?: number;

  constructor(private readonly output: vscode.OutputChannel) {}

  async start(opts: ServerStartOptions): Promise<void> {
    if (this.child && !this.child.killed) {
      // Reuse an in-process server if its port matches the request.
      if (this.currentPort === opts.port) {
        return;
      }
      // Different port asked: stop and respawn.
      await this.stop();
    }

    this.output.appendLine(
      `[solera] spawning: ${opts.command} (cwd=${opts.cwd}, port=${opts.port})`,
    );

    // Use shell so a multi-token `command` ("uv run python -m solera_mcp") works
    // without us needing to parse it. Hide the console window on Windows.
    const child = spawn(opts.command, {
      shell: true,
      cwd: opts.cwd,
      env: {
        ...process.env,
        SOLERA_MAP_PORT: String(opts.port),
        SOLERA_MAP_NO_MCP: "1",
      },
      windowsHide: true,
    });

    this.child = child;
    this.currentPort = opts.port;

    child.stdout?.on("data", (data: Buffer) => {
      this.output.append(data.toString());
    });
    child.stderr?.on("data", (data: Buffer) => {
      this.output.append(data.toString());
    });
    child.on("exit", (code, signal) => {
      this.output.appendLine(
        `[solera] server exited (code=${code} signal=${signal})`,
      );
      if (this.child === child) {
        this.child = undefined;
        this.currentPort = undefined;
      }
    });
    child.on("error", (err) => {
      this.output.appendLine(`[solera] spawn error: ${err.message}`);
    });

    // Poll /api/health until ready or timeout.
    await this.waitForHealth(opts.port);
  }

  async stop(): Promise<void> {
    const child = this.child;
    if (!child || child.killed) {
      this.child = undefined;
      this.currentPort = undefined;
      return;
    }
    this.output.appendLine("[solera] stopping server (SIGTERM)…");
    child.kill("SIGTERM");
    await new Promise<void>((resolve) => {
      const timer = setTimeout(() => {
        if (!child.killed) {
          this.output.appendLine("[solera] grace period expired; SIGKILL");
          child.kill("SIGKILL");
        }
        resolve();
      }, STOP_GRACE_MS);
      child.once("exit", () => {
        clearTimeout(timer);
        resolve();
      });
    });
    this.child = undefined;
    this.currentPort = undefined;
  }

  private async waitForHealth(port: number): Promise<void> {
    const deadline = Date.now() + HEALTH_TIMEOUT_MS;
    while (Date.now() < deadline) {
      // The exit listener (in start()) nulls `this.child` when the process
      // exits. Check that condition FIRST — otherwise the polling loop would
      // wait the full 15s instead of bailing out as soon as the child died.
      if (this.child === undefined) {
        throw new Error(
          'server process exited prematurely. See "Solera" output for details.',
        );
      }
      if (this.child.exitCode !== null && this.child.exitCode !== undefined) {
        throw new Error(
          `server process exited prematurely (code=${this.child.exitCode}). See "Solera" output for details.`,
        );
      }
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 800);
        const res = await fetch(`http://127.0.0.1:${port}/api/health`, {
          signal: controller.signal,
        });
        clearTimeout(timeout);
        if (res.ok) {
          this.output.appendLine(`[solera] server ready on :${port}`);
          return;
        }
      } catch {
        // Not ready yet — sleep and retry.
      }
      await new Promise((r) => setTimeout(r, HEALTH_POLL_MS));
    }
    throw new Error(
      `server did not become healthy within ${HEALTH_TIMEOUT_MS}ms. See "Solera" output for details.`,
    );
  }
}
