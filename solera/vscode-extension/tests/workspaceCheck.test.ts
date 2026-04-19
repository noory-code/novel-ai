import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { detectSoleraWorkspace } from "../src/workspaceCheck";

let tmpRoot: string;

beforeEach(async () => {
  tmpRoot = await fs.mkdtemp(path.join(os.tmpdir(), "solera-vscode-test-"));
});

afterEach(async () => {
  await fs.rm(tmpRoot, { recursive: true, force: true });
});

async function mkdirp(p: string): Promise<void> {
  await fs.mkdir(p, { recursive: true });
}

describe("detectSoleraWorkspace — happy paths", () => {
  it("returns kind 'v4' when .solera/concepts/ exists", async () => {
    await mkdirp(path.join(tmpRoot, ".solera", "concepts"));

    const finding = await detectSoleraWorkspace(tmpRoot);

    expect(finding.kind).toBe("v4");
    expect(finding.folderPath).toBe(tmpRoot);
    expect(finding.soleraRoot).toBe(path.join(tmpRoot, ".solera"));
  });

  it("returns kind 'v4' when .solera/identity/ exists (concepts may be empty in fresh setups)", async () => {
    await mkdirp(path.join(tmpRoot, ".solera", "identity"));

    const finding = await detectSoleraWorkspace(tmpRoot);

    expect(finding.kind).toBe("v4");
  });

  it("returns kind 'v3' when only workspace/concepts/ exists (no .solera/)", async () => {
    await mkdirp(path.join(tmpRoot, "workspace", "concepts"));

    const finding = await detectSoleraWorkspace(tmpRoot);

    expect(finding.kind).toBe("v3");
    expect(finding.soleraRoot).toBe(path.join(tmpRoot, "workspace"));
  });

  it("returns kind 'v3' when only workspace/identity/ exists", async () => {
    await mkdirp(path.join(tmpRoot, "workspace", "identity"));

    const finding = await detectSoleraWorkspace(tmpRoot);

    expect(finding.kind).toBe("v3");
  });

  it("returns kind 'none' when neither .solera/ nor workspace/ exists", async () => {
    // tmpRoot is empty.
    const finding = await detectSoleraWorkspace(tmpRoot);

    expect(finding.kind).toBe("none");
    expect(finding.soleraRoot).toBe("");
  });
});

describe("detectSoleraWorkspace — priority", () => {
  it("PREFERS .solera/ over workspace/ when both exist (mid-migration state)", async () => {
    await mkdirp(path.join(tmpRoot, ".solera", "concepts"));
    await mkdirp(path.join(tmpRoot, "workspace", "concepts"));

    const finding = await detectSoleraWorkspace(tmpRoot);

    expect(finding.kind).toBe("v4");
    expect(finding.soleraRoot).toBe(path.join(tmpRoot, ".solera"));
  });
});

describe("detectSoleraWorkspace — guards against false positives", () => {
  it("does NOT treat a workspace/ that contains only README.md as Solera (no concepts/, no identity/)", async () => {
    await mkdirp(path.join(tmpRoot, "workspace"));
    await fs.writeFile(path.join(tmpRoot, "workspace", "README.md"), "# notes");

    const finding = await detectSoleraWorkspace(tmpRoot);

    expect(finding.kind).toBe("none");
  });

  it("does NOT treat a .solera that exists as a FILE (not a dir) as Solera", async () => {
    await fs.writeFile(path.join(tmpRoot, ".solera"), "not a directory");

    const finding = await detectSoleraWorkspace(tmpRoot);

    expect(finding.kind).toBe("none");
  });

  it("does NOT treat a .solera/ where 'concepts' is a FILE (not a dir) as v4", async () => {
    await mkdirp(path.join(tmpRoot, ".solera"));
    await fs.writeFile(
      path.join(tmpRoot, ".solera", "concepts"),
      "stray file with the right name",
    );

    const finding = await detectSoleraWorkspace(tmpRoot);

    expect(finding.kind).toBe("none");
  });

  it("returns 'none' for a non-existent folder (does not throw)", async () => {
    const finding = await detectSoleraWorkspace(
      path.join(tmpRoot, "does-not-exist"),
    );

    expect(finding.kind).toBe("none");
  });
});

describe("detectSoleraWorkspace — partial v4 setup tolerated", () => {
  it("recognises v4 even when .solera/ has only one of concepts/identity (not both)", async () => {
    // Fresh init may seed concepts/ before identity/ depending on ordering.
    await mkdirp(path.join(tmpRoot, ".solera", "concepts"));

    const v4Only = await detectSoleraWorkspace(tmpRoot);
    expect(v4Only.kind).toBe("v4");

    // The opposite case.
    const tmpRoot2 = await fs.mkdtemp(path.join(os.tmpdir(), "solera-vscode-test-"));
    try {
      await mkdirp(path.join(tmpRoot2, ".solera", "identity"));
      const identityOnly = await detectSoleraWorkspace(tmpRoot2);
      expect(identityOnly.kind).toBe("v4");
    } finally {
      await fs.rm(tmpRoot2, { recursive: true, force: true });
    }
  });
});
