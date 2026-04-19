import * as fs from "node:fs";
import * as vscode from "vscode";
import { buildCsp, injectCspAndNonce, makeNonce, rewriteAssetUris } from "./csp";

export class MapPanel {
  private static current: MapPanel | undefined;
  private static onboardingCurrent: vscode.WebviewPanel | undefined;

  private readonly panel: vscode.WebviewPanel;
  private readonly disposables: vscode.Disposable[] = [];

  private constructor(panel: vscode.WebviewPanel) {
    this.panel = panel;
    panel.onDidDispose(() => this.dispose(), null, this.disposables);
  }

  static show(extensionUri: vscode.Uri, port: number, projectPath: string): void {
    if (MapPanel.current) {
      MapPanel.current.panel.reveal(vscode.ViewColumn.Active);
      MapPanel.current.refresh(extensionUri, port, projectPath);
      return;
    }
    const viewerRoot = vscode.Uri.joinPath(extensionUri, "media", "viewer");
    const panel = vscode.window.createWebviewPanel(
      "solera",
      "Solera",
      vscode.ViewColumn.Active,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        // localResourceRoots scopes the webview's `vscode-resource:` URIs.
        // Adding the viewer dir lets us load Vite-emitted JS/CSS bundles.
        localResourceRoots: [viewerRoot],
      },
    );
    MapPanel.current = new MapPanel(panel);
    MapPanel.current.refresh(extensionUri, port, projectPath);
  }

  static showOnboarding(extensionUri: vscode.Uri): void {
    if (MapPanel.onboardingCurrent) {
      MapPanel.onboardingCurrent.reveal(vscode.ViewColumn.Active);
      return;
    }
    const mediaUri = vscode.Uri.joinPath(extensionUri, "media");
    const panel = vscode.window.createWebviewPanel(
      "soleraOnboarding",
      "Solera — Setup",
      vscode.ViewColumn.Active,
      {
        enableScripts: false,
        localResourceRoots: [mediaUri],
      },
    );
    MapPanel.onboardingCurrent = panel;
    const onboardingPath = vscode.Uri.joinPath(mediaUri, "onboarding.html").fsPath;
    panel.webview.html = fs.readFileSync(onboardingPath, "utf-8");
    panel.onDidDispose(() => {
      MapPanel.onboardingCurrent = undefined;
    });
  }

  private refresh(extensionUri: vscode.Uri, port: number, projectPath: string): void {
    const viewerRoot = vscode.Uri.joinPath(extensionUri, "media", "viewer");
    const indexPath = vscode.Uri.joinPath(viewerRoot, "index.html").fsPath;
    if (!fs.existsSync(indexPath)) {
      this.panel.webview.html = errorHtml(
        "Viewer assets not found",
        `Expected media/viewer/index.html but it does not exist. ` +
          `Run 'npm run vscode:prepublish' to copy from ../viewer/dist/.`,
      );
      return;
    }

    const rawHtml = fs.readFileSync(indexPath, "utf-8");
    const toWebviewUri = (relPath: string): string => {
      const uri = vscode.Uri.joinPath(viewerRoot, relPath);
      return this.panel.webview.asWebviewUri(uri).toString();
    };
    const rewritten = rewriteAssetUris(rawHtml, toWebviewUri);

    const nonce = makeNonce();
    const csp = buildCsp(this.panel.webview.cspSource, nonce, port);
    const withCsp = injectCspAndNonce(rewritten, csp, nonce);

    // Inject a tiny bootstrap script that sets the project_path on the URL
    // before the React app's `resolveProjectPath()` runs. Using a query-string
    // bootstrap keeps the React code unchanged from the browser path.
    const bootstrap =
      `<script nonce="${nonce}">` +
      `(function(){var u=new URL(location.href);` +
      `u.searchParams.set('project_path',${JSON.stringify(projectPath)});` +
      `history.replaceState(null,'',u.toString());})();</script>`;
    const withBootstrap = withCsp.replace("</head>", `${bootstrap}\n</head>`);

    // The React app talks to http://127.0.0.1:{port}, NOT the webview's own
    // origin. Inject another tiny script that overrides `location.host` /
    // `location.protocol` lookups isn't viable in CSP — instead, add a meta
    // tag the React app can read. We don't need this in v0.1.0 because
    // viewer/api.ts already resolves URLs against `window.location`. But
    // since the webview's `window.location.host` is `vscode-webview://`, we
    // route via absolute http://127.0.0.1 URLs by overriding fetch + WebSocket
    // base. Done by setting a global hook the React app can opt into in a
    // later release. For now, the React app's relative paths (`/api/...`) hit
    // the webview origin and fail; the v0.1.0 workaround is the connect-src
    // CSP combined with a tiny patch in the bootstrap that overrides fetch
    // when the request URL starts with /api.
    const fetchPatch =
      `<script nonce="${nonce}">` +
      `(function(){var BASE='http://127.0.0.1:${port}';` +
      `var origFetch=window.fetch.bind(window);` +
      `window.fetch=function(input,init){` +
      `var url=typeof input==='string'?input:input.url;` +
      `if(url.startsWith('/api')){return origFetch(BASE+url,init);}` +
      `return origFetch(input,init);};` +
      `var OrigWS=window.WebSocket;` +
      `window.WebSocket=function(url,protocols){` +
      `if(typeof url==='string'&&url.startsWith('ws://')&&url.indexOf(location.host)>-1){` +
      `url='ws://127.0.0.1:${port}'+url.split(location.host).pop();}` +
      `return new OrigWS(url,protocols);};` +
      `window.WebSocket.prototype=OrigWS.prototype;})();</script>`;
    const final = withBootstrap.replace("</head>", `${fetchPatch}\n</head>`);

    this.panel.webview.html = final;
  }

  private dispose(): void {
    MapPanel.current = undefined;
    while (this.disposables.length) {
      const d = this.disposables.pop();
      d?.dispose();
    }
    this.panel.dispose();
  }
}

function errorHtml(title: string, body: string): string {
  return (
    "<!doctype html><html><head><meta charset=\"utf-8\"><title>" +
    escapeHtml(title) +
    "</title></head><body style=\"font-family:system-ui;padding:24px;color:#475569\">" +
    `<h1 style="font-size:18px;margin:0 0 8px">${escapeHtml(title)}</h1>` +
    `<p>${escapeHtml(body)}</p></body></html>`
  );
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
