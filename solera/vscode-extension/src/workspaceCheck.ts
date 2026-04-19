import * as fs from "node:fs/promises";
import * as path from "node:path";

export interface SoleraWorkspaceFinding {
  /** `v4`: `.solera/` exists. `v3`: only `workspace/` exists (deprecated). `none`: neither. */
  kind: "v4" | "v3" | "none";
  /** Absolute path of the workspace folder (the project root). */
  folderPath: string;
  /** Resolved Solera root (`.solera/` or `workspace/`); empty when `kind === "none"`. */
  soleraRoot: string;
}

const QUALIFYING_SUBDIRS = ["concepts", "identity"] as const;

/**
 * Detect whether `folderPath` is a Solera project. A directory qualifies if
 * it contains `concepts/` or `identity/`. v4 (`.solera/`) is preferred; v3
 * (`workspace/`) is reported separately so the caller can warn the user to
 * run `solera-migrate-workspace-to-dotsolera`.
 */
export async function detectSoleraWorkspace(
  folderPath: string,
): Promise<SoleraWorkspaceFinding> {
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
