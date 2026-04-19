import * as crypto from "node:crypto";

export function makeNonce(): string {
  return crypto.randomBytes(16).toString("base64");
}

/**
 * Build the Content-Security-Policy meta tag for the webview.
 *
 * - `default-src 'none'` — fail closed.
 * - `script-src 'nonce-...'` — only inline/embedded scripts carrying the
 *   per-load nonce may execute. (vsce will reject extensions that allow
 *   `unsafe-inline` without a nonce.)
 * - `style-src` includes `'unsafe-inline'` because Tailwind's reset injects
 *   inline `<style>` blocks at runtime; locking this down would require a
 *   build-time CSS extraction we don't ship in v0.1.0.
 * - `connect-src` opens localhost ports for the React app to reach the
 *   spawned server. This is the documented trust boundary trade-off — see
 *   README's "Security model" section.
 * - `img-src` allows the webview's resource scheme + data URIs (icons).
 * - `font-src` mirrors style-src for any web fonts referenced by Tailwind.
 */
export function buildCsp(webviewCspSource: string, nonce: string, port: number): string {
  return [
    "default-src 'none'",
    `script-src 'nonce-${nonce}'`,
    `style-src ${webviewCspSource} 'unsafe-inline'`,
    `img-src ${webviewCspSource} data:`,
    `font-src ${webviewCspSource}`,
    `connect-src http://127.0.0.1:${port} ws://127.0.0.1:${port}`,
  ].join("; ");
}

/**
 * Rewrite the asset URLs in a viewer `index.html` so they resolve through the
 * VSCode webview resource scheme. Vite emits `<script src="/assets/..."`
 * style references that won't load otherwise.
 */
export function rewriteAssetUris(
  html: string,
  toWebviewUri: (relPath: string) => string,
): string {
  // Match src="/assets/..." and href="/assets/..." (anchored to a leading slash).
  return html
    .replace(/(<script\b[^>]*\bsrc=)["']\/(assets\/[^"']+)["']/g, (_, lead, asset) => {
      return `${lead}"${toWebviewUri(asset)}"`;
    })
    .replace(/(<link\b[^>]*\bhref=)["']\/(assets\/[^"']+)["']/g, (_, lead, asset) => {
      return `${lead}"${toWebviewUri(asset)}"`;
    });
}

/**
 * Add the CSP meta tag and the per-load nonce to every script tag in `html`.
 */
export function injectCspAndNonce(html: string, csp: string, nonce: string): string {
  const cspMeta = `<meta http-equiv="Content-Security-Policy" content="${csp}">`;
  // Inject the CSP just after <head>.
  let out = html.replace(/<head>/i, `<head>\n  ${cspMeta}`);
  // Add the nonce attribute to every <script> tag (Vite's emitted ones).
  out = out.replace(/<script\b/g, `<script nonce="${nonce}"`);
  return out;
}
