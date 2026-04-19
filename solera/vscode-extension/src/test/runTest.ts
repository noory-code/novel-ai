import * as path from "node:path";
import { runTests } from "@vscode/test-electron";

/**
 * Entry point for VSCode extension integration tests.
 *
 * Launches a clean VSCode instance (downloaded on first run), installs this
 * extension, and runs the mocha suite under src/test/suite/. Unlike vitest
 * unit tests — which mock the `vscode` module — these tests run inside a
 * real VSCode host and exercise the Extension Host APIs (Webview, workspace,
 * commands).
 *
 * Invoked via `npm run test:integration`.
 */
async function main(): Promise<void> {
  try {
    // Resolve paths once — everything is relative to this compiled file
    // living under out/test/.
    const extensionDevelopmentPath = path.resolve(__dirname, "../../");
    const extensionTestsPath = path.resolve(__dirname, "./suite/index");

    // Launch VSCode with the extension loaded, pointing at no workspace
    // (tests create their own tmpdirs and open folders programmatically).
    //
    // Pin to the same minimum version the extension manifest declares as
    // its `engines.vscode` — newer VSCodes occasionally break
    // @vscode/test-electron's Electron-argument forwarding on macOS
    // (1.116 rejects flags with "bad option: --extensionTestsPath"); 1.85
    // is the floor we already commit to supporting.
    await runTests({
      version: "1.85.0",
      extensionDevelopmentPath,
      extensionTestsPath,
      // --disable-extensions keeps the host clean — only our extension
      // under test is loaded; stops user-installed extensions from
      // interfering with CI runs.
      launchArgs: ["--disable-extensions"],
    });
  } catch (err) {
    console.error("Failed to run integration tests:", err);
    process.exit(1);
  }
}

void main();
