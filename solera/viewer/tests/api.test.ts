import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  fetchGraph,
  fetchLayout,
  patchConcept,
  proposeConceptFromNarrative,
  resolveProjectPath,
  saveLayout,
} from "../src/api";

const okJson = (body: unknown): Response =>
  ({
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  }) as unknown as Response;

const errJson = (status: number, error: string): Response =>
  ({
    ok: false,
    status,
    json: () => Promise.resolve({ error }),
  }) as unknown as Response;

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

// ---------------------------------------------------------------------------
// fetchGraph
// ---------------------------------------------------------------------------

describe("fetchGraph", () => {
  it("URL-encodes the project_path", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(okJson({ concepts: [] })));
    vi.stubGlobal("fetch", fetchMock);

    await fetchGraph("/path with spaces/banas");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/graph?project_path=%2Fpath%20with%20spaces%2Fbanas",
    );
  });

  it("returns the parsed body when 2xx", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(okJson({ concepts: [{ id: "auth" }] }))),
    );

    const graph = await fetchGraph("/proj");

    expect(graph.concepts).toEqual([{ id: "auth" }]);
  });

  it("throws server-provided error on non-2xx", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(errJson(404, "workspace not found"))),
    );

    await expect(fetchGraph("/proj")).rejects.toThrow("workspace not found");
  });

  it("falls back to HTTP status text when error body is malformed", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        () =>
          Promise.resolve({
            ok: false,
            status: 503,
            json: () => Promise.reject(new Error("not json")),
          }) as Promise<Response>,
      ),
    );

    await expect(fetchGraph("/proj")).rejects.toThrow("HTTP 503");
  });
});

// ---------------------------------------------------------------------------
// fetchLayout
// ---------------------------------------------------------------------------

describe("fetchLayout", () => {
  it("returns parsed layout on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(okJson({ nodes: { "concept:auth": { x: 12, y: 34 } } })),
      ),
    );

    const layout = await fetchLayout("/proj");

    expect(layout.nodes["concept:auth"]).toEqual({ x: 12, y: 34 });
  });

  it("returns empty layout (does NOT throw) on error — the layout is non-critical", async () => {
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(errJson(404, "no layout"))));

    const layout = await fetchLayout("/proj");

    expect(layout).toEqual({ nodes: {} });
  });
});

// ---------------------------------------------------------------------------
// saveLayout
// ---------------------------------------------------------------------------

describe("saveLayout", () => {
  it("PUTs JSON-encoded layout body", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(okJson({ ok: true })));
    vi.stubGlobal("fetch", fetchMock);

    await saveLayout("/proj", { nodes: { foo: { x: 1, y: 2 } } });

    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toBe("/api/layout?project_path=%2Fproj");
    expect(init?.method).toBe("PUT");
    expect(init?.headers).toEqual({ "Content-Type": "application/json" });
    expect(JSON.parse(init?.body as string)).toEqual({
      nodes: { foo: { x: 1, y: 2 } },
    });
  });

  it("throws on non-2xx", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(errJson(400, "bad layout"))),
    );

    await expect(saveLayout("/proj", { nodes: {} })).rejects.toThrow("bad layout");
  });
});

// ---------------------------------------------------------------------------
// patchConcept
// ---------------------------------------------------------------------------

describe("patchConcept", () => {
  it("URL-encodes both concept_id and project_path", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(okJson({ ok: true })));
    vi.stubGlobal("fetch", fetchMock);

    await patchConcept("/proj path", "concept/with/slash", { parent: "p" });

    const [url] = fetchMock.mock.calls[0];
    expect(String(url)).toBe(
      "/api/concept/concept%2Fwith%2Fslash?project_path=%2Fproj%20path",
    );
  });

  it("PATCHes the parent field as-is (including null to clear)", async () => {
    const fetchMock = vi.fn(() => Promise.resolve(okJson({ ok: true })));
    vi.stubGlobal("fetch", fetchMock);

    await patchConcept("/proj", "child", { parent: null });

    const init = fetchMock.mock.calls[0][1];
    expect(init?.method).toBe("PATCH");
    expect(JSON.parse(init?.body as string)).toEqual({ parent: null });
  });

  it("throws on non-2xx with the server's error message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(errJson(400, "would create a cycle"))),
    );

    await expect(patchConcept("/proj", "a", { parent: "b" })).rejects.toThrow(
      "would create a cycle",
    );
  });
});

// ---------------------------------------------------------------------------
// proposeConceptFromNarrative — the Moment 1 guardrail entry point
// ---------------------------------------------------------------------------

describe("proposeConceptFromNarrative", () => {
  it("POSTs snake_case body keys (matching the server contract)", async () => {
    const fetchMock = vi.fn(() =>
      Promise.resolve(okJson({ ok: true, concept_id: "x", needs_intent_review: true })),
    );
    vi.stubGlobal("fetch", fetchMock);

    await proposeConceptFromNarrative("/proj", {
      narrativeId: "rush-orders",
      conceptId: "order-tracking",
      conceptName: "Order Tracking",
    });

    const init = fetchMock.mock.calls[0][1];
    expect(init?.method).toBe("POST");
    expect(JSON.parse(init?.body as string)).toEqual({
      narrative_id: "rush-orders",
      concept_id: "order-tracking",
      concept_name: "Order Tracking",
    });
  });

  it("returns the parsed result so the caller can show 'needs review' UI", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve(
          okJson({
            ok: true,
            concept_path: ".solera/concepts/order-tracking.md",
            concept_id: "order-tracking",
            needs_intent_review: true,
          }),
        ),
      ),
    );

    const result = await proposeConceptFromNarrative("/proj", {
      narrativeId: "rush-orders",
      conceptId: "order-tracking",
      conceptName: "Order Tracking",
    });

    expect(result.ok).toBe(true);
    expect(result.needs_intent_review).toBe(true);
    expect(result.concept_path).toBe(".solera/concepts/order-tracking.md");
  });

  it("surfaces server validation errors (e.g. concept_id collision) verbatim", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(errJson(409, "Concept 'order-tracking' already exists. Use a different id"))),
    );

    await expect(
      proposeConceptFromNarrative("/proj", {
        narrativeId: "rush-orders",
        conceptId: "order-tracking",
        conceptName: "Order Tracking",
      }),
    ).rejects.toThrow(/already exists/);
  });
});

// ---------------------------------------------------------------------------
// resolveProjectPath — reads from URL search params
// ---------------------------------------------------------------------------

describe("resolveProjectPath", () => {
  it("reads project_path from query string", () => {
    history.replaceState(null, "", "/?project_path=/foo/bar");
    expect(resolveProjectPath()).toBe("/foo/bar");
  });

  it("falls back to legacy `project` alias", () => {
    history.replaceState(null, "", "/?project=/legacy");
    expect(resolveProjectPath()).toBe("/legacy");
  });

  it("returns empty string when neither key is present", () => {
    history.replaceState(null, "", "/");
    expect(resolveProjectPath()).toBe("");
  });
});
