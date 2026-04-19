import * as assert from "node:assert";
import * as fs from "node:fs/promises";
import * as os from "node:os";
import * as path from "node:path";
import * as vscode from "vscode";

/**
 * Integration tests for the Solera VSCode extension.
 *
 * These tests run inside a real VSCode Extension Host (launched by
 * @vscode/test-electron) and exercise behaviors that cannot be unit-tested:
 *
 * - The extension activates on command invocation.
 * - `solera.open` is registered as a contributes command.
 * - Configuration settings (`solera.command`, `solera.port`) are
 *   readable via vscode.workspace.getConfiguration.
 * - The onboarding webview opens when no `.solera/` or `workspace/` is
 *   present in the workspace root.
 *
 * What these tests do NOT cover:
 * - Actual server spawn (requires `uv` on PATH in the CI environment).
 * - Webview Content-Security-Policy enforcement (VSCode test-electron
 *   doesn't expose the rendered DOM in a scriptable way).
 * - End-user interaction with the React viewer running inside the
 *   webview (out of scope — that's browser automation territory).
 */

// --- helpers ---------------------------------------------------------------

function waitMs(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function closeAllWebviews(): Promise<void> {
  // Closes all editor tabs (including webview panels). `workbench.action.
  // closeAllEditors` is VSCode's canonical command for this; it's a no-op
  // when there are no open editors.
  await vscode.commands.executeCommand("workbench.action.closeAllEditors");
  await waitMs(100);
}

// --- suite -----------------------------------------------------------------

suite("Solera extension — activation", () => {
  test("extension is installed and discoverable by id", () => {
    // The publisher+name pair in package.json resolves here:
    // publisher 'noory-code' + name 'solera' → 'noory-code.solera'.
    const ext = vscode.extensions.getExtension("noory-code.solera");
    assert.ok(ext, "extension 'noory-code.solera' not found in host");
  });

  test("activates when the solera.open command is invoked (even from an empty host)", async () => {
    const ext = vscode.extensions.getExtension("noory-code.solera");
    assert.ok(ext);

    if (!ext.isActive) {
      // Execute the contributed command once — VSCode auto-generates an
      // activation event from contributes.commands since 1.74, so invoking
      // the command triggers activate().
      try {
        await vscode.commands.executeCommand("solera.open");
      } catch {
        // The command may show an error dialog (no workspace folder) —
        // that's fine for THIS assertion. We only care that activate() ran.
      }
      // Give VSCode a moment to complete the activation promise.
      for (let i = 0; i < 20 && !ext.isActive; i++) {
        await waitMs(100);
      }
    }

    assert.strictEqual(ext.isActive, true, "extension did not activate");
  });
});

suite("Solera extension — commands", () => {
  test("registers `solera.open` in the command palette", async () => {
    const commands = await vscode.commands.getCommands(true);
    assert.ok(
      commands.includes("solera.open"),
      "solera.open command not registered",
    );
  });
});

suite("Solera extension — configuration", () => {
  test("exposes `solera.command` with the documented default", () => {
    const config = vscode.workspace.getConfiguration("solera");
    const command = config.get<string>("command");
    assert.strictEqual(command, "uv run python -m solera_mcp");
  });

  test("exposes `solera.port` with the documented default", () => {
    const config = vscode.workspace.getConfiguration("solera");
    const port = config.get<number>("port");
    assert.strictEqual(port, 5170);
  });
});

suite("Solera extension — onboarding when no workspace folder", () => {
  // No workspace is open at this point (runTest.ts launches without one).
  // Invoking the command must surface an error, not crash.
  test("shows an error message when no folder is open", async () => {
    let shown = false;
    const originalShowError = vscode.window.showErrorMessage;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (vscode.window as any).showErrorMessage = async (msg: string): Promise<undefined> => {
      if (msg.toLowerCase().includes("folder") || msg.toLowerCase().includes("workspace")) {
        shown = true;
      }
      return undefined;
    };
    try {
      await vscode.commands.executeCommand("solera.open");
      // Give the command a moment to enter its no-folders branch.
      await waitMs(200);
      assert.strictEqual(
        shown,
        true,
        "expected an error message about missing workspace folder",
      );
    } finally {
      vscode.window.showErrorMessage = originalShowError;
    }
  });
});

suite("Solera extension — onboarding for non-Solera folders", () => {
  let tmpRoot: string;

  suiteSetup(async () => {
    tmpRoot = await fs.mkdtemp(path.join(os.tmpdir(), "solera-int-"));
    // Folder exists but has no `.solera/` and no `workspace/` — detectSolera
    // Workspace returns kind: "none", the extension should open onboarding.
    await fs.writeFile(path.join(tmpRoot, "README.md"), "# empty project");
  });

  suiteTeardown(async () => {
    await fs.rm(tmpRoot, { recursive: true, force: true });
  });

  test("opens the onboarding webview for a folder with no Solera data", async function () {
    // This test rewrites workspace folders at runtime, which can take a
    // few seconds on slow machines; bump the mocha-level timeout.
    this.timeout(20_000);

    const tmpUri = vscode.Uri.file(tmpRoot);
    const ok = vscode.workspace.updateWorkspaceFolders(
      0,
      (vscode.workspace.workspaceFolders ?? []).length,
      { uri: tmpUri, name: "empty-project" },
    );
    assert.strictEqual(ok, true, "updateWorkspaceFolders refused the change");

    // The workspace-folder update is async — poll until VSCode reflects it.
    for (let i = 0; i < 30; i++) {
      if ((vscode.workspace.workspaceFolders ?? []).length > 0) break;
      await waitMs(100);
    }
    assert.strictEqual(
      vscode.workspace.workspaceFolders?.[0].uri.fsPath,
      tmpRoot,
    );

    await closeAllWebviews();
    await vscode.commands.executeCommand("solera.open");

    // The onboarding panel is created via createWebviewPanel with viewType
    // 'soleraOnboarding'. Wait for it to appear.
    let found = false;
    for (let i = 0; i < 30; i++) {
      const tabs = vscode.window.tabGroups.all.flatMap((g) => g.tabs);
      if (
        tabs.some(
          (t) => t.label === "Solera — Setup" || t.label.includes("Setup"),
        )
      ) {
        found = true;
        break;
      }
      await waitMs(100);
    }

    assert.strictEqual(
      found,
      true,
      `expected a webview tab titled 'Solera — Setup' for non-Solera folder. ` +
        `Open tab labels: ${vscode.window.tabGroups.all
          .flatMap((g) => g.tabs.map((t) => t.label))
          .join(", ")}`,
    );

    await closeAllWebviews();
  });
});
