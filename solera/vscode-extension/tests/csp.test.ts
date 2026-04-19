import { describe, expect, it } from "vitest";
import {
  buildCsp,
  injectCspAndNonce,
  makeNonce,
  rewriteAssetUris,
} from "../src/csp";

// ---------------------------------------------------------------------------
// makeNonce
// ---------------------------------------------------------------------------

describe("makeNonce", () => {
  it("returns base64-decodable strings of consistent length", () => {
    const nonce = makeNonce();
    // 16 random bytes → 24-char base64 (with padding).
    expect(nonce).toHaveLength(24);
    // Round-trip through base64 to confirm it's valid.
    const decoded = Buffer.from(nonce, "base64");
    expect(decoded).toHaveLength(16);
  });

  it("returns a different value on each call (enough entropy to be safe)", () => {
    const seen = new Set<string>();
    for (let i = 0; i < 100; i++) {
      seen.add(makeNonce());
    }
    expect(seen.size).toBe(100);
  });
});

// ---------------------------------------------------------------------------
// buildCsp
// ---------------------------------------------------------------------------

describe("buildCsp", () => {
  it("includes a default-src 'none' fail-closed directive", () => {
    const csp = buildCsp("vscode-resource:scheme", "ABC123", 5170);
    expect(csp).toMatch(/default-src 'none'/);
  });

  it("scopes script execution to the per-load nonce only", () => {
    const csp = buildCsp("vscode-resource:scheme", "ABC123", 5170);
    expect(csp).toContain("script-src 'nonce-ABC123'");
    // No `unsafe-inline` for scripts — nonce is the only escape hatch.
    expect(csp).not.toMatch(/script-src[^;]*'unsafe-inline'/);
  });

  it("opens connect-src to the configured localhost port via http AND ws", () => {
    const csp = buildCsp("vscode-resource:scheme", "ABC123", 5170);
    expect(csp).toContain("connect-src http://127.0.0.1:5170 ws://127.0.0.1:5170");
  });

  it("uses the supplied port (not the default)", () => {
    const csp = buildCsp("vscode-resource:scheme", "ABC123", 9999);
    expect(csp).toContain("http://127.0.0.1:9999");
    expect(csp).toContain("ws://127.0.0.1:9999");
  });

  it("references the webview's CSP source for style/img/font", () => {
    const source = "vscode-resource:host";
    const csp = buildCsp(source, "ABC123", 5170);
    expect(csp).toContain(`style-src ${source}`);
    expect(csp).toContain(`img-src ${source}`);
    expect(csp).toContain(`font-src ${source}`);
  });
});

// ---------------------------------------------------------------------------
// rewriteAssetUris
// ---------------------------------------------------------------------------

describe("rewriteAssetUris", () => {
  const toWebviewUri = (rel: string): string => `vscode-webview://abc/media/viewer/${rel}`;

  it("rewrites <script src='/assets/...'> URLs through the webview scheme", () => {
    const html = `<script type="module" src="/assets/index-CnD1y5Iy.js"></script>`;
    const out = rewriteAssetUris(html, toWebviewUri);
    expect(out).toContain(
      'src="vscode-webview://abc/media/viewer/assets/index-CnD1y5Iy.js"',
    );
  });

  it("rewrites <link href='/assets/...'> URLs (CSS bundles)", () => {
    const html = `<link rel="stylesheet" href="/assets/index-Cqe2AYvF.css">`;
    const out = rewriteAssetUris(html, toWebviewUri);
    expect(out).toContain(
      'href="vscode-webview://abc/media/viewer/assets/index-Cqe2AYvF.css"',
    );
  });

  it("does NOT rewrite asset paths that don't start with a leading slash", () => {
    const html = `<script src="assets/index.js"></script>`;
    const out = rewriteAssetUris(html, toWebviewUri);
    // No rewrite — the regex anchors on a leading "/".
    expect(out).toContain('src="assets/index.js"');
  });

  it("does NOT rewrite tags that aren't <script> or <link>", () => {
    const html = `<a href="/assets/foo">link</a>`;
    const out = rewriteAssetUris(html, toWebviewUri);
    expect(out).toBe(html);
  });

  it("rewrites multiple asset references in the same document", () => {
    const html =
      `<link rel="stylesheet" href="/assets/a.css">` +
      `<script type="module" src="/assets/b.js"></script>`;
    const out = rewriteAssetUris(html, toWebviewUri);
    expect(out).toContain('href="vscode-webview://abc/media/viewer/assets/a.css"');
    expect(out).toContain('src="vscode-webview://abc/media/viewer/assets/b.js"');
  });
});

// ---------------------------------------------------------------------------
// injectCspAndNonce
// ---------------------------------------------------------------------------

describe("injectCspAndNonce", () => {
  it("inserts the CSP meta tag immediately after <head>", () => {
    const html = `<!doctype html><html><head><title>X</title></head><body></body></html>`;
    const csp = "default-src 'none'";
    const out = injectCspAndNonce(html, csp, "NONCE");

    expect(out).toContain(
      `<head>\n  <meta http-equiv="Content-Security-Policy" content="${csp}">`,
    );
  });

  it("adds the nonce attribute to every <script> tag", () => {
    const html =
      `<head></head><body>` +
      `<script src="/a.js"></script>` +
      `<script type="module" src="/b.js"></script>` +
      `</body>`;
    const out = injectCspAndNonce(html, "csp", "ABC123");

    // Both scripts get the nonce; original attributes preserved.
    const matches = out.match(/<script nonce="ABC123"/g);
    expect(matches).toHaveLength(2);
    expect(out).toContain('<script nonce="ABC123" src="/a.js"');
    expect(out).toContain('<script nonce="ABC123" type="module" src="/b.js"');
  });

  it("does NOT add a nonce to non-script tags", () => {
    const html = `<head></head><body><div>x</div><a href="">y</a></body>`;
    const out = injectCspAndNonce(html, "csp", "NONCE");
    // No nonce attribute outside of <script>.
    expect(out.match(/nonce="NONCE"/g)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// Composition test — full transformation pipeline
// ---------------------------------------------------------------------------

describe("CSP pipeline composition", () => {
  it("produces a webview-loadable HTML where scripts have nonces and assets resolve through asWebviewUri", () => {
    const rawHtml =
      `<!doctype html><html lang="en"><head>` +
      `<meta charset="utf-8"><title>Solera</title>` +
      `<script type="module" src="/assets/index-CnD1y5Iy.js"></script>` +
      `<link rel="stylesheet" href="/assets/index-Cqe2AYvF.css">` +
      `</head><body><div id="root"></div></body></html>`;

    const toWebviewUri = (rel: string): string =>
      `vscode-webview://test/media/viewer/${rel}`;
    const nonce = "TESTNONCE";
    const csp = buildCsp("vscode-webview://test", nonce, 5170);

    const rewritten = rewriteAssetUris(rawHtml, toWebviewUri);
    const final = injectCspAndNonce(rewritten, csp, nonce);

    // CSP meta tag landed in <head>.
    expect(final).toContain(`<meta http-equiv="Content-Security-Policy"`);
    // Scripts have nonce.
    expect(final).toContain(`<script nonce="${nonce}"`);
    // Assets routed through the webview scheme.
    expect(final).toContain(
      'vscode-webview://test/media/viewer/assets/index-CnD1y5Iy.js',
    );
    expect(final).toContain(
      'vscode-webview://test/media/viewer/assets/index-Cqe2AYvF.css',
    );
    // Localhost connection allowed for the React app to talk to the server.
    expect(final).toContain("connect-src http://127.0.0.1:5170");
  });
});
