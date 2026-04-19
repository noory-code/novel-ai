import type { Graph, Layout } from "./types";

const API_BASE = "";

export async function fetchGraph(projectPath: string): Promise<Graph> {
  const url = `${API_BASE}/api/graph?project_path=${encodeURIComponent(projectPath)}`;
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(body?.error ?? `HTTP ${res.status}`);
  }
  return (await res.json()) as Graph;
}

export async function fetchLayout(projectPath: string): Promise<Layout> {
  const url = `${API_BASE}/api/layout?project_path=${encodeURIComponent(projectPath)}`;
  const res = await fetch(url);
  if (!res.ok) {
    return { nodes: {} };
  }
  return (await res.json()) as Layout;
}

export async function saveLayout(projectPath: string, layout: Layout): Promise<void> {
  const url = `${API_BASE}/api/layout?project_path=${encodeURIComponent(projectPath)}`;
  const res = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(layout),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(body?.error ?? `HTTP ${res.status}`);
  }
}

export async function patchConcept(
  projectPath: string,
  conceptId: string,
  patch: { parent?: string | null },
): Promise<void> {
  const url = `${API_BASE}/api/concept/${encodeURIComponent(
    conceptId,
  )}?project_path=${encodeURIComponent(projectPath)}`;
  const res = await fetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(body?.error ?? `HTTP ${res.status}`);
  }
}

export interface ProposeConceptResult {
  ok: true;
  concept_path: string;
  concept_id: string;
  needs_intent_review: true;
}

/**
 * Create a stub Concept proposed from a Narrative. The server flags the new
 * Concept's `# Intent` as "needs human review per solera-write-concept Moment 1
 * rule" — the human must run `solera-write-concept update` to fill it. This
 * surfaces the canvas action without bypassing the Moment 1 collaboration rule.
 */
export async function proposeConceptFromNarrative(
  projectPath: string,
  body: { narrativeId: string; conceptId: string; conceptName: string },
): Promise<ProposeConceptResult> {
  const url = `${API_BASE}/api/concept/propose-from-narrative?project_path=${encodeURIComponent(
    projectPath,
  )}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      narrative_id: body.narrativeId,
      concept_id: body.conceptId,
      concept_name: body.conceptName,
    }),
  });
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(errBody?.error ?? `HTTP ${res.status}`);
  }
  return (await res.json()) as ProposeConceptResult;
}

export interface GraphSocket {
  close(): void;
}

export function openGraphSocket(
  projectPath: string,
  onEvent: (event: { event: string }) => void,
  onError: (err: string) => void,
): GraphSocket {
  const wsProto = window.location.protocol === "https:" ? "wss" : "ws";
  const host = window.location.host;
  const url = `${wsProto}://${host}/ws?project_path=${encodeURIComponent(projectPath)}`;
  const ws = new WebSocket(url);

  ws.onmessage = (e) => {
    try {
      onEvent(JSON.parse(e.data));
    } catch {
      onError("malformed message");
    }
  };
  ws.onerror = () => onError("websocket error");
  ws.onclose = (e) => {
    if (e.code !== 1000 && e.code !== 1001) {
      onError(`connection closed (${e.code})`);
    }
  };

  return { close: () => ws.close() };
}

export function resolveProjectPath(): string {
  const params = new URLSearchParams(window.location.search);
  return params.get("project_path") ?? params.get("project") ?? "";
}
