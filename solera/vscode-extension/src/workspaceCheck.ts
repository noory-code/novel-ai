import * as fs from "node:fs/promises";
import * as path from "node:path";

export interface SoleraWorkspaceFinding {
  /** `r9`: `.noory/solera/` exists (preferred).
   *  `v4`: legacy `.solera/` exists; the server will auto-migrate it.
   *  `v3`: only `workspace/` exists (deprecated).
   *  `none`: neither. */
  kind: "r9" | "v4" | "v3" | "none";
  /** Absolute path of the workspace folder (the project root). */
  folderPath: string;
  /** Resolved Solera root (`.noory/solera/`, `.solera/`, or `workspace/`);
   *  empty when `kind === "none"`. */
  soleraRoot: string;
}

const QUALIFYING_SUBDIRS = ["concepts", "identity"] as const;

/**
 * Detect whether `folderPath` is a Solera project. A directory qualifies if
 * it contains `concepts/` or `identity/`. `.noory/solera/` (R9, preferred)
 * is checked first; a legacy `.solera/` is reported as `v4` and will be
 * auto-migrated by the Python server on first read; v3 (`workspace/`) is
 * reported separately so the caller can warn the user to run
 * `solera-migrate-workspace-to-dotsolera`.
 */
export async function detectSoleraWorkspace(
  folderPath: string,
): Promise<SoleraWorkspaceFinding> {
  const r9Root = path.join(folderPath, ".noory", "solera");
  if (await hasSoleraQualifier(r9Root)) {
    return { kind: "r9", folderPath, soleraRoot: r9Root };
  }
  if (await hasSoleraQualifier(path.join(folderPath, ".solera"))) {
    return {
      kind: "v4",
      folderPath,
      soleraRoot: path.join(folderPath, ".solera"),
    };
  }
  if (await hasSoleraQualifier(path.join(folderPath, "workspace"))) {
    return {
      kind: "v3",
      folderPath,
      soleraRoot: path.join(folderPath, "workspace"),
    };
  }
  return { kind: "none", folderPath, soleraRoot: "" };
}

async function hasSoleraQualifier(dirPath: string): Promise<boolean> {
  try {
    const stat = await fs.stat(dirPath);
    if (!stat.isDirectory()) return false;
  } catch {
    return false;
  }
  for (const child of QUALIFYING_SUBDIRS) {
    try {
      const childStat = await fs.stat(path.join(dirPath, child));
      if (childStat.isDirectory()) return true;
    } catch {
      // ignore — try next qualifier
    }
  }
  return false;
}
