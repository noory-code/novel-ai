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

export type SocketStatus = "connecting" | "connected" | "reconnecting" | "disconnected";

export interface GraphSocketHandlers {
  onEvent: (event: { event: string }) => void;
  onStatus?: (status: SocketStatus) => void;
  onError?: (err: string) => void;
}

/**
 * Open a resilient graph WebSocket with exponential-backoff reconnection.
 *
 * Backoff doubles from 1s up to 30s; each reconnect attempt emits
 * ``status: "reconnecting"`` and then ``"connected"`` on success. Normal
 * close codes (1000 ``going away``, 1001 ``endpoint terminating``) don't
 * trigger retries — those are user-initiated teardowns. Policy violations
 * (1008) and bad payloads (1003) also stop retrying since the server
 * explicitly rejected the session.
 */
export function openGraphSocket(
  projectPath: string,
  handlers: GraphSocketHandlers,
): GraphSocket {
  const wsProto = window.location.protocol === "https:" ? "wss" : "ws";
  const host = window.location.host;
  const url = `${wsProto}://${host}/ws?project_path=${encodeURIComponent(projectPath)}`;
  const { onEvent, onStatus, onError } = handlers;

  let ws: WebSocket | null = null;
  let disposed = false;
  let retryMs = 1000;
  const RETRY_MAX = 30_000;
  let retryTimer: number | null = null;

  const report = (status: SocketStatus) => onStatus?.(status);

  const scheduleReconnect = () => {
    if (disposed) return;
    report("reconnecting");
    retryTimer = window.setTimeout(() => {
      retryTimer = null;
      connect();
    }, retryMs);
    retryMs = Math.min(retryMs * 2, RETRY_MAX);
  };

  const connect = () => {
    if (disposed) return;
    report(retryMs === 1000 ? "connecting" : "reconnecting");
    const socket = new WebSocket(url);
    ws = socket;

    socket.onopen = () => {
      retryMs = 1000;
      report("connected");
    };
    socket.onmessage = (e) => {
      try {
        onEvent(JSON.parse(e.data));
      } catch {
        onError?.("malformed message");
      }
    };
    socket.onerror = () => {
      // Deferred to onclose — onerror alone doesn't give a close code and
      // fires during the same lifecycle event as onclose on socket failures.
    };
    socket.onclose = (e) => {
      ws = null;
      if (disposed) return;
      const normal = e.code === 1000 || e.code === 1001;
      const rejected = e.code === 1003 || e.code === 1008;
      if (normal || rejected) {
        report("disconnected");
        if (rejected) onError?.(`connection rejected (${e.code}) ${e.reason}`.trim());
        return;
      }
      onError?.(`connection lost (${e.code})`);
      scheduleReconnect();
    };
  };

  connect();

  return {
    close: () => {
      disposed = true;
      if (retryTimer !== null) window.clearTimeout(retryTimer);
      if (ws !== null) ws.close(1000, "client closing");
      report("disconnected");
    },
  };
}

export function resolveProjectPath(): string {
  const params = new URLSearchParams(window.location.search);
  return params.get("project_path") ?? params.get("project") ?? "";
}
