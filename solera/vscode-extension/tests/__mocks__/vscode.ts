// Minimal stub of the `vscode` module surface our extension uses. The real
// module is provided by the VSCode host at runtime — these stubs cover the
// API points exercised by unit tests (csp.ts, workspaceCheck.ts,
// ServerProcess.ts). MapPanel.ts and extension.ts use richer surface
// (Webview, ExtensionContext) that we do NOT exercise here — those need
// `@vscode/test-electron` integration tests.

import { vi } from "vitest";

export class Uri {
  static joinPath(base: Uri, ...parts: string[]): Uri {
    return new Uri(`${base.toString()}/${parts.join("/")}`.replace(/\/+/g, "/"));
  }
  static file(path: string): Uri {
    return new Uri(path);
  }
  static parse(s: string): Uri {
    return new Uri(s);
  }
  constructor(public readonly value: string) {}
  toString(): string {
    return this.value;
  }
  get fsPath(): string {
    return this.value;
  }
}

export const window = {
  createOutputChannel: vi.fn((name: string) => ({
    name,
    appendLine: vi.fn(),
    append: vi.fn(),
    show: vi.fn(),
    dispose: vi.fn(),
  })),
  showErrorMessage: vi.fn(() => Promise.resolve(undefined)),
  showInformationMessage: vi.fn(() => Promise.resolve(undefined)),
  showQuickPick: vi.fn(() => Promise.resolve(undefined)),
  createWebviewPanel: vi.fn(),
};

export const workspace = {
  workspaceFolders: undefined as undefined | { uri: Uri }[],
  getConfiguration: vi.fn(() => ({
    get: vi.fn(<T>(_key: string, fallback: T) => fallback),
  })),
};

export const commands = {
  registerCommand: vi.fn(() => ({ dispose: vi.fn() })),
  executeCommand: vi.fn(),
};

export const ViewColumn = {
  Active: -1,
  Beside: -2,
  One: 1,
};

export const Disposable = class {
  static from(...items: { dispose(): void }[]) {
    return { dispose: () => items.forEach((i) => i.dispose()) };
  }
  dispose(): void {}
};

export type ExtensionContext = {
  subscriptions: { dispose(): void }[];
  extensionUri: Uri;
};
