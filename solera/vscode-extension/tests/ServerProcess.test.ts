import { EventEmitter } from "node:events";
import { beforeEach, describe, expect, it, vi } from "vitest";

// node:child_process is mocked BEFORE importing ServerProcess so the import
// inside ServerProcess.ts picks up our fake `spawn`.
vi.mock("node:child_process", () => {
  return {
    spawn: vi.fn(),
  };
});

import { spawn } from "node:child_process";
import { ServerProcess } from "../src/ServerProcess";

// Helper: a minimal fake ChildProcess emitter the tests can drive.
class FakeChildProcess extends EventEmitter {
  killed = false;
  exitCode: number | null = null;
  stdout = new EventEmitter();
  stderr = new EventEmitter();
  kill(signal?: NodeJS.Signals | number): boolean {
    // Simulate POSIX behavior: SIGTERM triggers exit; SIGKILL is the bigger hammer.
    this.killed = true;
    setImmediate(() => {
      this.exitCode = signal === "SIGKILL" ? 137 : 143;
      this.emit("exit", this.exitCode, signal ?? null);
    });
    return true;
  }
}

const mockOutput = () => ({
  appendLine: vi.fn(),
  append: vi.fn(),
  show: vi.fn(),
  dispose: vi.fn(),
  name: "test",
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
}) as any;

const mkChild = (): FakeChildProcess => new FakeChildProcess();

beforeEach(() => {
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

// ---------------------------------------------------------------------------
// start() — happy path
// ---------------------------------------------------------------------------

describe("ServerProcess.start — health probe", () => {
  it("returns successfully when /api/health returns 200 within timeout", async () => {
    const child = mkChild();
    vi.mocked(spawn).mockReturnValue(child as never);

    const fetchMock = vi.fn(() =>
      Promise.resolve({ ok: true } as Response),
    );
    vi.stubGlobal("fetch", fetchMock);

    const proc = new ServerProcess(mockOutput());
    await proc.start({
      command: "uv run python -m solera_mcp",
      cwd: "/proj",
      port: 5170,
    });

    expect(spawn).toHaveBeenCalledWith(
      "uv run python -m solera_mcp",
      expect.objectContaining({
        shell: true,
        cwd: "/proj",
        env: expect.objectContaining({
          SOLERA_MAP_PORT: "5170",
          SOLERA_MAP_NO_MCP: "1",
        }),
        windowsHide: true,
      }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "http://127.0.0.1:5170/api/health",
      expect.any(Object),
    );

    await proc.stop();
  });

  it("sets SOLERA_MAP_NO_MCP=1 so the spawned server skips stdio MCP", async () => {
    const child = mkChild();
    vi.mocked(spawn).mockReturnValue(child as never);
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true } as Response)));

    const proc = new ServerProcess(mockOutput());
    await proc.start({ command: "x", cwd: "/p", port: 5170 });

    const env = vi.mocked(spawn).mock.calls[0][1]?.env as NodeJS.ProcessEnv;
    expect(env.SOLERA_MAP_NO_MCP).toBe("1");

    await proc.stop();
  });
});

// ---------------------------------------------------------------------------
// start() — failure modes
// ---------------------------------------------------------------------------

describe("ServerProcess.start — failure modes", () => {
  it("throws when the child exits before health becomes ready", async () => {
    const child = mkChild();
    vi.mocked(spawn).mockReturnValue(child as never);

    // fetch always 500 so we keep polling until the child dies.
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve({ ok: false, status: 500 } as Response)),
    );

    const proc = new ServerProcess(mockOutput());
    const startPromise = proc.start({
      command: "x",
      cwd: "/p",
      port: 5170,
    });

    // Simulate the spawned process crashing immediately.
    setImmediate(() => {
      child.exitCode = 1;
      child.emit("exit", 1, null);
    });

    await expect(startPromise).rejects.toThrow(/exited prematurely/);
  });
});

// ---------------------------------------------------------------------------
// start() — reuse semantics
// ---------------------------------------------------------------------------

describe("ServerProcess.start — reuse", () => {
  it("does NOT spawn a second child when called again with the same port", async () => {
    const child = mkChild();
    vi.mocked(spawn).mockReturnValue(child as never);
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true } as Response)));

    const proc = new ServerProcess(mockOutput());
    await proc.start({ command: "x", cwd: "/p", port: 5170 });
    await proc.start({ command: "x", cwd: "/p", port: 5170 });

    expect(spawn).toHaveBeenCalledTimes(1);

    await proc.stop();
  });

  it("respawns when called with a different port", async () => {
    const first = mkChild();
    const second = mkChild();
    vi.mocked(spawn)
      .mockReturnValueOnce(first as never)
      .mockReturnValueOnce(second as never);
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true } as Response)));

    const proc = new ServerProcess(mockOutput());
    await proc.start({ command: "x", cwd: "/p", port: 5170 });
    await proc.start({ command: "x", cwd: "/p", port: 6000 });

    expect(spawn).toHaveBeenCalledTimes(2);
    // First child got SIGTERM during the respawn.
    expect(first.killed).toBe(true);

    await proc.stop();
  });
});

// ---------------------------------------------------------------------------
// stop()
// ---------------------------------------------------------------------------

describe("ServerProcess.stop", () => {
  it("sends SIGTERM and resolves once the child exits within grace", async () => {
    const child = mkChild();
    vi.mocked(spawn).mockReturnValue(child as never);
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true } as Response)));

    const proc = new ServerProcess(mockOutput());
    await proc.start({ command: "x", cwd: "/p", port: 5170 });

    const killSpy = vi.spyOn(child, "kill");
    await proc.stop();

    expect(killSpy).toHaveBeenCalledWith("SIGTERM");
  });

  it("is idempotent — stop() called twice doesn't throw", async () => {
    const child = mkChild();
    vi.mocked(spawn).mockReturnValue(child as never);
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true } as Response)));

    const proc = new ServerProcess(mockOutput());
    await proc.start({ command: "x", cwd: "/p", port: 5170 });

    await proc.stop();
    await expect(proc.stop()).resolves.toBeUndefined();
  });

  it("handles stop() called before start() (no child to kill)", async () => {
    const proc = new ServerProcess(mockOutput());
    await expect(proc.stop()).resolves.toBeUndefined();
    expect(spawn).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// stdout/stderr forwarding
// ---------------------------------------------------------------------------

describe("ServerProcess output channel forwarding", () => {
  it("appends child stdout chunks to the output channel", async () => {
    const child = mkChild();
    vi.mocked(spawn).mockReturnValue(child as never);
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true } as Response)));

    const out = mockOutput();
    const proc = new ServerProcess(out);
    await proc.start({ command: "x", cwd: "/p", port: 5170 });

    child.stdout.emit("data", Buffer.from("hello from server\n"));

    expect(out.append).toHaveBeenCalledWith("hello from server\n");

    await proc.stop();
  });

  it("appends child stderr chunks to the output channel too", async () => {
    const child = mkChild();
    vi.mocked(spawn).mockReturnValue(child as never);
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve({ ok: true } as Response)));

    const out = mockOutput();
    const proc = new ServerProcess(out);
    await proc.start({ command: "x", cwd: "/p", port: 5170 });

    child.stderr.emit("data", Buffer.from("traceback...\n"));

    expect(out.append).toHaveBeenCalledWith("traceback...\n");

    await proc.stop();
  });
});
