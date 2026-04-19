import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";
import Mocha from "mocha";
import { glob } from "glob";

/**
 * Mocha entry. Called by @vscode/test-electron once VSCode is up with our
 * extension activated. Discovers *.test.js files compiled from the
 * src/test/suite/ directory and runs them.
 *
 * Logs to a file because @vscode/test-electron swallows stdout/stderr from
 * the extension host — on failure the caller only sees "Exit code: 1".
 * The log file lands in the OS tmp dir so it's inspectable after the run.
 */
const logPath = path.join(os.tmpdir(), "solera-vscode-integration.log");

function tee(msg: string): void {
  console.log(msg);
  try {
    fs.appendFileSync(logPath, msg + "\n");
  } catch {
    // Ignore logging failures — they shouldn't mask test outcomes.
  }
}

export async function run(): Promise<void> {
  // Truncate the log file at the start of each run.
  try {
    fs.writeFileSync(logPath, "");
  } catch {
    // ignore
  }

  tee(`[integration] log file: ${logPath}`);

  const mocha = new Mocha({
    ui: "tdd",
    color: true,
    timeout: 60_000, // generous — spawning a real server can take a second
    reporter: "spec",
  });

  const testsRoot = path.resolve(__dirname, ".");
  tee(`[integration] testsRoot: ${testsRoot}`);

  // Compiled files land alongside index.js in out/test/suite/.
  const files = await glob("**/*.test.js", { cwd: testsRoot });
  tee(`[integration] discovered test files: ${files.join(", ") || "(none)"}`);
  files.forEach((file) => mocha.addFile(path.resolve(testsRoot, file)));

  return new Promise<void>((resolve, reject) => {
    try {
      mocha.run((failures: number) => {
        tee(`[integration] mocha finished with ${failures} failure(s)`);
        if (failures > 0) {
          reject(new Error(`${failures} test(s) failed. See ${logPath}.`));
        } else {
          resolve();
        }
      });
    } catch (err) {
      tee(`[integration] fatal: ${err instanceof Error ? err.stack ?? err.message : String(err)}`);
      reject(err);
    }
  });
}
