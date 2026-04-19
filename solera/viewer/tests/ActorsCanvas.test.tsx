import { describe, expect, it } from "vitest";
import { buildActorsFlowElements } from "../src/canvases/ActorsCanvas";
import type {
  Graph,
  Identity,
  Journey,
  Layout,
  Narrative,
  Persona,
  Role,
} from "../src/types";

const mkRole = (id: string, overrides: Partial<Role> = {}): Role => ({
  id,
  name: id.replace(/-/g, " "),
  status: "active",
  description: `Description of ${id}.`,
  context: null,
  parent: null,
  integrity: [],
  ...overrides,
});

const mkPersona = (
  id: string,
  role: string,
  overrides: Partial<Persona> = {},
): Persona => ({
  id,
  name: id.replace(/-/g, " "),
  status: "active",
  role,
  identity: `Identity for ${id}.`,
  goals: [],
  pains: [],
  triggers: [],
  quotes: [],
  channels: null,
  parent: null,
  integrity: [],
  ...overrides,
});

const mkJourney = (id: string, walks: string, overrides: Partial<Journey> = {}): Journey => ({
  id,
  name: id.replace(/-/g, " "),
  status: "active",
  walks,
  walked_by: [],
  trigger: `Trigger for ${id}.`,
  steps: [],
  outcome: `Outcome for ${id}.`,
  parent: null,
  integrity: [],
  ...overrides,
});

const mkNarrative = (id: string, overrides: Partial<Narrative> = {}): Narrative => ({
  id,
  form: "user_story",
  status: "active",
  statement: `As a user, I want ${id}.`,
  context: `Context for ${id}.`,
  acceptance_cues: [],
  about_roles: ["customer"],
  about_personas: [],
  in_journey: null,
  proposes: [],
  integrity: [],
  ...overrides,
});

const emptyIdentity: Identity = {
  mission: null,
  vision: null,
  values: null,
  goals: null,
  tone_and_manner: null,
  extras: {},
};

const filledIdentity: Identity = {
  ...emptyIdentity,
  mission: "A test mission.",
};

const baseGraph = (overrides: Partial<Graph> = {}): Graph => ({
  identity: emptyIdentity,
  roles: [],
  personas: [],
  journeys: [],
  narratives: [],
  concepts: [],
  concept_edges: [],
  milestones: [],
  stories: [],
  action_items: [],
  releases: [],
  ...overrides,
});

const emptyLayout: Layout = { nodes: {} };

describe("buildActorsFlowElements — happy paths", () => {
  it("places a single top-level Role at 12 o'clock on the first ring", () => {
    // emptyIdentity renders no Identity hub, so the first Role is the only node.
    const graph = baseGraph({ roles: [mkRole("admin")] });

    const { nodes } = buildActorsFlowElements(graph, emptyLayout, null);

    expect(nodes).toHaveLength(1);
    expect(nodes[0].id).toBe("role:admin");
    expect(nodes[0].position.x).toBeCloseTo(0, 3);
    // With Identity absent the origin is not occupied; the first Role still
    // lands at the "12 o'clock" slot (negative y = north on screen).
    expect(nodes[0].position.y).toBeLessThan(0);
  });

  it("renders Identity hub + Role ring + archetype Persona + walks edge", () => {
    const graph = baseGraph({
      identity: filledIdentity,
      roles: [mkRole("fan")],
      personas: [mkPersona("alice", "fan")],
      journeys: [mkJourney("first-purchase", "fan")],
    });

    const { nodes, edges } = buildActorsFlowElements(graph, emptyLayout, null);

    expect(nodes.map((n) => n.id).sort()).toEqual([
      "identity",
      "journey:first-purchase",
      "persona:alice",
      "role:fan",
    ]);
    expect(edges.find((e) => e.id === "identity-fan")).toBeDefined();
    expect(edges.find((e) => e.id === "role-persona-alice")).toMatchObject({
      source: "role:fan",
      target: "persona:alice",
    });
    expect(edges.find((e) => e.id === "walks-first-purchase")).toMatchObject({
      source: "role:fan",
      target: "journey:first-purchase",
      label: "walks",
    });
  });

  it("anchors a Narrative to its in_journey via a dashed edge", () => {
    const graph = baseGraph({
      roles: [mkRole("fan")],
      journeys: [mkJourney("first-purchase", "fan")],
      narratives: [
        mkNarrative("rush-orders", {
          about_roles: ["fan"],
          in_journey: "first-purchase",
        }),
      ],
    });

    const { edges } = buildActorsFlowElements(graph, emptyLayout, null);

    const inJourneyEdge = edges.find((e) => e.id === "in-journey-rush-orders");
    expect(inJourneyEdge).toMatchObject({
      source: "journey:first-purchase",
      target: "narrative:rush-orders",
    });
    expect(inJourneyEdge?.style?.strokeDasharray).toBeDefined();
  });

  it("falls back to about_roles[0] anchor when a Narrative has no in_journey", () => {
    const graph = baseGraph({
      roles: [mkRole("fan")],
      narratives: [mkNarrative("loose", { about_roles: ["fan"] })],
    });

    const { edges } = buildActorsFlowElements(graph, emptyLayout, null);

    const aboutEdge = edges.find((e) => e.id === "about-role-loose-fan");
    expect(aboutEdge).toMatchObject({
      source: "role:fan",
      target: "narrative:loose",
    });
  });

  it("emits a walked_by edge from Journey to concrete Persona archetype", () => {
    const graph = baseGraph({
      roles: [mkRole("fan")],
      personas: [mkPersona("alice", "fan")],
      journeys: [mkJourney("first-purchase", "fan", { walked_by: ["alice"] })],
    });

    const { edges } = buildActorsFlowElements(graph, emptyLayout, null);

    const walkedByEdge = edges.find(
      (e) => e.id === "walked-by-first-purchase-alice",
    );
    expect(walkedByEdge).toMatchObject({
      source: "journey:first-purchase",
      target: "persona:alice",
    });
  });
});

describe("buildActorsFlowElements — orphan handling", () => {
  it("does NOT emit a walks edge when the named Role is missing", () => {
    const graph = baseGraph({
      journeys: [mkJourney("ghost-walk", "missing-role")],
    });

    const { nodes, edges } = buildActorsFlowElements(graph, emptyLayout, null);

    expect(nodes.find((n) => n.id === "journey:ghost-walk")).toBeDefined();
    expect(edges.find((e) => e.id.startsWith("walks-"))).toBeUndefined();
  });

  it("renders Journey with empty walks field without crashing", () => {
    const graph = baseGraph({
      roles: [mkRole("fan")],
      journeys: [mkJourney("broken", "")],
    });

    const { nodes, edges } = buildActorsFlowElements(graph, emptyLayout, null);

    expect(nodes.find((n) => n.id === "journey:broken")).toBeDefined();
    expect(edges.find((e) => e.id === "walks-broken")).toBeUndefined();
  });

  it("does NOT emit any anchor edge for a Narrative with no journey AND no known role", () => {
    const graph = baseGraph({
      narratives: [mkNarrative("homeless", { about_roles: ["ghost-role"] })],
    });

    const { edges } = buildActorsFlowElements(graph, emptyLayout, null);

    expect(edges).toHaveLength(0);
  });

  it("Persona with missing Role still renders (orphan row); no role-persona edge", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice", "missing-role")],
    });

    const { nodes, edges } = buildActorsFlowElements(graph, emptyLayout, null);

    expect(nodes.find((n) => n.id === "persona:alice")).toBeDefined();
    expect(edges.find((e) => e.id === "role-persona-alice")).toBeUndefined();
  });
});

describe("buildActorsFlowElements — persisted layout", () => {
  it("uses persisted positions over auto-layout when present", () => {
    const graph = baseGraph({ roles: [mkRole("admin")] });
    const layout: Layout = { nodes: { "role:admin": { x: 999, y: -42 } } };

    const { nodes } = buildActorsFlowElements(graph, layout, null);

    const role = nodes.find((n) => n.id === "role:admin");
    expect(role?.position).toEqual({ x: 999, y: -42 });
  });

  it("only uses stored coordinates when BOTH x and y are present", () => {
    const graph = baseGraph({ roles: [mkRole("admin")] });
    const layout: Layout = { nodes: { "role:admin": { x: 999 } } };

    const { nodes } = buildActorsFlowElements(graph, layout, null);

    const role = nodes.find((n) => n.id === "role:admin");
    expect(role?.position.x).not.toBe(999);
  });
});

describe("buildActorsFlowElements — selection highlighting", () => {
  it("renders the same node ids regardless of selection", () => {
    const graph = baseGraph({
      roles: [mkRole("fan")],
      journeys: [mkJourney("first-purchase", "fan")],
    });

    const without = buildActorsFlowElements(graph, emptyLayout, null);
    const withSel = buildActorsFlowElements(graph, emptyLayout, {
      kind: "role",
      id: "fan",
    });

    expect(withSel.nodes.map((n) => n.id)).toEqual(
      without.nodes.map((n) => n.id),
    );
    expect(withSel.edges.map((e) => e.id)).toEqual(
      without.edges.map((e) => e.id),
    );
  });
});

describe("buildActorsFlowElements — Role parent chain", () => {
  it("emits a parent-role edge for each child Role", () => {
    const graph = baseGraph({
      roles: [
        mkRole("general-user"),
        mkRole("fan", { parent: "general-user" }),
      ],
    });

    const { edges } = buildActorsFlowElements(graph, emptyLayout, null);

    const parentEdge = edges.find((e) => e.id === "parent-role-fan");
    expect(parentEdge).toMatchObject({
      source: "role:general-user",
      target: "role:fan",
    });
  });

  it("groups Journeys with their walks Role", () => {
    const graph = baseGraph({
      roles: [mkRole("admin"), mkRole("fan")],
      journeys: [
        mkJourney("admin-1", "admin"),
        mkJourney("fan-1", "fan"),
        mkJourney("fan-2", "fan"),
      ],
    });

    const { edges } = buildActorsFlowElements(graph, emptyLayout, null);

    const walksEdges = edges.filter((e) => e.id.startsWith("walks-"));
    expect(walksEdges).toHaveLength(3);
    expect(
      walksEdges.find((e) => e.target === "journey:admin-1")?.source,
    ).toBe("role:admin");
    expect(
      walksEdges.find((e) => e.target === "journey:fan-1")?.source,
    ).toBe("role:fan");
  });
});

describe("buildActorsFlowElements — proposes signal", () => {
  it("does not emit edges to Concepts (Concepts live on a different canvas)", () => {
    const graph = baseGraph({
      roles: [mkRole("fan")],
      narratives: [
        mkNarrative("seed", { about_roles: ["fan"], proposes: ["new-concept"] }),
      ],
    });

    const { edges } = buildActorsFlowElements(graph, emptyLayout, null);

    expect(
      edges.find((e) => String(e.target).startsWith("concept:")),
    ).toBeUndefined();
  });
});
