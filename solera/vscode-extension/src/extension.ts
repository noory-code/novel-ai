import * as vscode from "vscode";
import { MapPanel } from "./MapPanel";
import { ServerProcess } from "./ServerProcess";
import { detectSoleraWorkspace, type SoleraWorkspaceFinding } from "./workspaceCheck";

let serverProcess: ServerProcess | undefined;
let outputChannel: vscode.OutputChannel | undefined;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
  outputChannel = vscode.window.createOutputChannel("Solera");
  context.subscriptions.push(outputChannel);

  const openCommand = vscode.commands.registerCommand("solera.open", async () => {
    await openMap(context);
  });
  context.subscriptions.push(openCommand);
}

export async function deactivate(): Promise<void> {
  await serverProcess?.stop();
  serverProcess = undefined;
}

async function openMap(context: vscode.ExtensionContext): Promise<void> {
  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    void vscode.window.showErrorMessage(
      "Solera: open a folder or workspace first.",
    );
    return;
  }

  // Probe each folder for a Solera workspace. If exactly one matches, use it.
  // If multiple, ask. If none, show onboarding.
  const findings: SoleraWorkspaceFinding[] = [];
  for (const folder of folders) {
    const finding = await detectSoleraWorkspace(folder.uri.fsPath);
    if (finding.kind !== "none") findings.push(finding);
  }

  if (findings.length === 0) {
    MapPanel.showOnboarding(context.extensionUri);
    return;
  }

  let chosen: SoleraWorkspaceFinding;
  if (findings.length === 1) {
    chosen = findings[0];
  } else {
    const pick = await vscode.window.showQuickPick(
      findings.map((f) => ({
        label: f.folderPath.split("/").pop() ?? f.folderPath,
        description: f.folderPath,
        finding: f,
      })),
      { placeHolder: "Multiple Solera-bearing folders found — choose one" },
    );
    if (!pick) return;
    chosen = pick.finding;
  }

  if (chosen.kind === "v3") {
    void vscode.window.showInformationMessage(
      "This project still uses the v3 `workspace/` layout. " +
        "Run `/solera-migrate-workspace-to-dotsolera` in Claude Code to relocate to `.noory/solera/`. " +
        "(Solera reads both layouts; the workspace/ fallback will be dropped in a future minor.)",
      "Continue anyway",
    );
  }

  const port = vscode.workspace
    .getConfiguration("solera")
    .get<number>("port", 5170);

  const command = vscode.workspace
    .getConfiguration("solera")
    .get<string>("command", "uv run python -m solera_mcp");

  // Reuse an existing server if one is healthy on the configured port; spawn
  // otherwise. The probe avoids double-launching when Claude Code MCP already
  // started the server in the same project.
  const alreadyRunning = await probeHealth(port);
  if (!alreadyRunning) {
    if (!serverProcess) {
      serverProcess = new ServerProcess(outputChannel!);
    }
    try {
      await serverProcess.start({
        command,
        cwd: chosen.folderPath,
        port,
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      void vscode.window.showErrorMessage(
        `Solera: failed to start server (${msg}). ` +
          `Check that 'uv' is on PATH and the solera-mcp package is resolvable.`,
        "Open Output",
      );
      outputChannel?.show(true);
      return;
    }
  }

  MapPanel.show(context.extensionUri, port, chosen.folderPath);
}

async function probeHealth(port: number): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 1000);
    const res = await fetch(`http://127.0.0.1:${port}/api/health`, {
      signal: controller.signal,
    });
    clearTimeout(timeout);
    return res.ok;
  } catch {
    return false;
  }
}
