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

// ---------------------------------------------------------------------------
// CRUD client — v5.1 unified POST/PATCH surface
// ---------------------------------------------------------------------------

/**
 * Low-level caller for a PATCH against ``/api/{kind}/{id}``. Unwraps
 * the server error body and throws on any non-2xx so callers can rely
 * on ``await patchX(...)`` always succeeding if it returns.
 */
async function patchEntity(
  projectPath: string,
  kind: string,
  entityId: string,
  patch: Record<string, unknown>,
): Promise<void> {
  const url = `${API_BASE}/api/${kind}/${encodeURIComponent(
    entityId,
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

/** Low-level caller for ``POST /api/{kind}``. Returns the new id on success. */
async function createEntity(
  projectPath: string,
  kind: string,
  payload: Record<string, unknown>,
): Promise<{ ok: true; id: string; path: string }> {
  const url = `${API_BASE}/api/${kind}?project_path=${encodeURIComponent(projectPath)}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(body?.error ?? `HTTP ${res.status}`);
  }
  return (await res.json()) as { ok: true; id: string; path: string };
}

// Concept — extended in v5.1 to accept every allowed field (name, status,
// intent, current_design, current_shape, horizon, parent). The signature is
// loose so callers can patch one field at a time.
export interface ConceptPatch {
  name?: string;
  status?: "active" | "deprecated" | "archived";
  intent?: string;
  current_design?: string;
  current_shape?: string;
  horizon?: string | null;
  parent?: string | null;
}

export function patchConcept(
  projectPath: string,
  conceptId: string,
  patch: ConceptPatch,
): Promise<void> {
  return patchEntity(projectPath, "concept", conceptId, patch as unknown as Record<string, unknown>);
}

export interface ConceptCreate {
  id: string;
  name?: string;
  intent?: string;
  current_design?: string;
  current_shape?: string;
  horizon?: string;
  parent?: string;
}
export function createConcept(projectPath: string, payload: ConceptCreate) {
  return createEntity(projectPath, "concept", payload as unknown as Record<string, unknown>);
}

// Role
export interface RolePatch {
  name?: string;
  status?: "active" | "deprecated" | "archived";
  description?: string;
  context?: string | null;
  parent?: string | null;
}
export function patchRole(projectPath: string, roleId: string, patch: RolePatch) {
  return patchEntity(projectPath, "role", roleId, patch as unknown as Record<string, unknown>);
}
export interface RoleCreate {
  id: string;
  name?: string;
  description?: string;
  context?: string;
  parent?: string;
}
export function createRole(projectPath: string, payload: RoleCreate) {
  return createEntity(projectPath, "role", payload as unknown as Record<string, unknown>);
}

// Persona
export interface PersonaPatch {
  name?: string;
  status?: "active" | "deprecated" | "archived";
  role?: string;
  identity?: string;
  goals?: string[];
  pains?: string[];
  triggers?: string[];
  quotes?: string[];
  channels?: string | null;
  parent?: string | null;
}
export function patchPersona(projectPath: string, personaId: string, patch: PersonaPatch) {
  return patchEntity(projectPath, "persona", personaId, patch as unknown as Record<string, unknown>);
}
export interface PersonaCreate {
  id: string;
  role: string;
  name?: string;
  identity?: string;
  goals?: string[];
  pains?: string[];
  triggers?: string[];
  quotes?: string[];
  channels?: string;
  parent?: string;
}
export function createPersona(projectPath: string, payload: PersonaCreate) {
  return createEntity(projectPath, "persona", payload as unknown as Record<string, unknown>);
}

// Journey
export interface JourneyStepInput {
  n: number;
  stage: string;
  step: string;
  touchpoint: string;
  emotion: string;
  pain: string;
}
export interface JourneyPatch {
  name?: string;
  status?: "active" | "deprecated" | "archived";
  walks?: string;
  walked_by?: string[];
  trigger?: string;
  steps?: JourneyStepInput[];
  outcome?: string;
  parent?: string | null;
}
export function patchJourney(projectPath: string, journeyId: string, patch: JourneyPatch) {
  return patchEntity(projectPath, "journey", journeyId, patch as unknown as Record<string, unknown>);
}
export interface JourneyCreate {
  id: string;
  walks: string;
  walked_by?: string[];
  name?: string;
  trigger?: string;
  steps?: JourneyStepInput[];
  outcome?: string;
  parent?: string;
}
export function createJourney(projectPath: string, payload: JourneyCreate) {
  return createEntity(projectPath, "journey", payload as unknown as Record<string, unknown>);
}

// Narrative
export interface NarrativePatch {
  name?: string;
  status?: "active" | "deprecated" | "archived";
  form?: "user_story" | "jtbd" | "scenario";
  statement?: string;
  context?: string;
  acceptance_cues?: string[];
  about_roles?: string[];
  about_personas?: string[];
  in_journey?: string | null;
  proposes?: string[];
}
export function patchNarrative(projectPath: string, narrativeId: string, patch: NarrativePatch) {
  return patchEntity(projectPath, "narrative", narrativeId, patch as unknown as Record<string, unknown>);
}
export interface NarrativeCreate {
  id: string;
  about_roles: string[];
  form?: "user_story" | "jtbd" | "scenario";
  about_personas?: string[];
  statement?: string;
  context?: string;
  acceptance_cues?: string[];
  in_journey?: string;
  proposes?: string[];
}
export function createNarrative(projectPath: string, payload: NarrativeCreate) {
  return createEntity(projectPath, "narrative", payload as unknown as Record<string, unknown>);
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
