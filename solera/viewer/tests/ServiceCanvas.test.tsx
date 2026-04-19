import { describe, expect, it } from "vitest";
import { buildServiceFlowElements } from "../src/canvases/ServiceCanvas";
import type {
  Graph,
  Identity,
  Journey,
  Layout,
  Narrative,
  Persona,
} from "../src/types";

const mkPersona = (id: string, overrides: Partial<Persona> = {}): Persona => ({
  id,
  name: id.replace(/-/g, " "),
  status: "active",
  role: "customer",
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

describe("buildServiceFlowElements — happy paths", () => {
  it("renders a Persona node with the expected id and position when no layout override exists", () => {
    const graph = baseGraph({ personas: [mkPersona("alice")] });

    const { nodes, edges } = buildServiceFlowElements(graph, emptyLayout, null);

    expect(nodes).toHaveLength(1);
    expect(nodes[0].id).toBe("persona:alice");
    expect(nodes[0].position).toEqual({ x: 0, y: 0 });
    expect(edges).toHaveLength(0);
  });

  it("emits a `walks` edge when a Journey points at an active Persona", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      journeys: [mkJourney("first-purchase", "alice")],
    });

    const { nodes, edges } = buildServiceFlowElements(graph, emptyLayout, null);

    expect(nodes.map((n) => n.id).sort()).toEqual([
      "journey:first-purchase",
      "persona:alice",
    ]);
    expect(edges).toHaveLength(1);
    expect(edges[0]).toMatchObject({
      id: "walks-first-purchase",
      source: "persona:alice",
      target: "journey:first-purchase",
      label: "walks",
    });
  });

  it("anchors a Narrative to its in_journey via a dashed edge", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      journeys: [mkJourney("first-purchase", "alice")],
      narratives: [
        mkNarrative("rush-orders", { in_journey: "first-purchase" }),
      ],
    });

    const { edges } = buildServiceFlowElements(graph, emptyLayout, null);

    const inJourneyEdge = edges.find((e) => e.id === "in-journey-rush-orders");
    expect(inJourneyEdge).toBeDefined();
    expect(inJourneyEdge?.source).toBe("journey:first-purchase");
    expect(inJourneyEdge?.target).toBe("narrative:rush-orders");
    // Dashed style for anchor edges.
    expect(inJourneyEdge?.style?.strokeDasharray).toBeDefined();
  });

  it("falls back to about_personas[0] anchor when a Narrative has no in_journey", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      narratives: [mkNarrative("loose", { about_personas: ["alice"] })],
    });

    const { edges } = buildServiceFlowElements(graph, emptyLayout, null);

    const aboutEdge = edges.find((e) => e.id === "about-loose-alice");
    expect(aboutEdge).toBeDefined();
    expect(aboutEdge?.source).toBe("persona:alice");
    expect(aboutEdge?.target).toBe("narrative:loose");
  });
});

describe("buildServiceFlowElements — orphan handling", () => {
  it("does NOT emit a walks edge when the named Persona is missing (orphan Journey)", () => {
    const graph = baseGraph({
      // No personas; journey walks a ghost.
      journeys: [mkJourney("ghost-walk", "missing-persona")],
    });

    const { nodes, edges } = buildServiceFlowElements(graph, emptyLayout, null);

    expect(nodes.find((n) => n.id === "journey:ghost-walk")).toBeDefined();
    // No walks edge because the Persona doesn't exist.
    expect(edges.find((e) => e.id.startsWith("walks-"))).toBeUndefined();
  });

  it("renders Journey with `walks: ''` (empty walks field) without crashing", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      journeys: [mkJourney("broken", "")], // empty walks
    });

    const { nodes, edges } = buildServiceFlowElements(graph, emptyLayout, null);

    expect(nodes.find((n) => n.id === "journey:broken")).toBeDefined();
    expect(edges.find((e) => e.id === "walks-broken")).toBeUndefined();
  });

  it("does NOT emit any anchor edge for a Narrative with no journey AND no known persona", () => {
    const graph = baseGraph({
      // Persona "alice" missing entirely; narrative is fully orphaned.
      narratives: [mkNarrative("homeless", { about_personas: ["alice"] })],
    });

    const { edges } = buildServiceFlowElements(graph, emptyLayout, null);

    expect(edges).toHaveLength(0);
  });
});

describe("buildServiceFlowElements — persisted layout", () => {
  it("uses persisted positions over auto-layout when present", () => {
    const graph = baseGraph({ personas: [mkPersona("alice")] });
    const layout: Layout = {
      nodes: { "persona:alice": { x: 999, y: -42 } },
    };

    const { nodes } = buildServiceFlowElements(graph, layout, null);

    expect(nodes[0].position).toEqual({ x: 999, y: -42 });
  });

  it("only uses stored coordinates when BOTH x and y are present", () => {
    const graph = baseGraph({ personas: [mkPersona("alice")] });
    const layout: Layout = {
      // Only x — y missing → treated as if no override (auto-layout wins).
      nodes: { "persona:alice": { x: 999 } },
    };

    const { nodes } = buildServiceFlowElements(graph, layout, null);

    expect(nodes[0].position).toEqual({ x: 0, y: 0 });
  });
});

describe("buildServiceFlowElements — selection highlighting", () => {
  it("renders the same node ids regardless of selection (selection only affects style)", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      journeys: [mkJourney("first-purchase", "alice")],
    });

    const withoutSelection = buildServiceFlowElements(graph, emptyLayout, null);
    const withSelection = buildServiceFlowElements(graph, emptyLayout, {
      kind: "persona",
      id: "alice",
    });

    expect(withSelection.nodes.map((n) => n.id)).toEqual(
      withoutSelection.nodes.map((n) => n.id),
    );
    // Identical edge set too — selection never gates which entities appear.
    expect(withSelection.edges.map((e) => e.id)).toEqual(
      withoutSelection.edges.map((e) => e.id),
    );
  });
});

describe("buildServiceFlowElements — multiple personas / journeys", () => {
  it("groups Journeys with their walks Persona (each gets a walks edge)", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice"), mkPersona("bob")],
      journeys: [
        mkJourney("alice-1", "alice"),
        mkJourney("alice-2", "alice"),
        mkJourney("bob-1", "bob"),
      ],
    });

    const { edges } = buildServiceFlowElements(graph, emptyLayout, null);

    const walksEdges = edges.filter((e) => e.id.startsWith("walks-"));
    expect(walksEdges).toHaveLength(3);
    expect(walksEdges.find((e) => e.target === "journey:alice-1")?.source).toBe("persona:alice");
    expect(walksEdges.find((e) => e.target === "journey:alice-2")?.source).toBe("persona:alice");
    expect(walksEdges.find((e) => e.target === "journey:bob-1")?.source).toBe("persona:bob");
  });

  it("renders narratives in their journey's column even when the journey is owned by a different persona", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice"), mkPersona("bob")],
      journeys: [mkJourney("alice-1", "alice")],
      // Narrative "about: bob" but anchored to alice's journey — perfectly
      // valid (a narrative may concern a Persona who doesn't walk that
      // particular Journey, even if it's an unusual data shape).
      narratives: [mkNarrative("crossover", { about_personas: ["bob"], in_journey: "alice-1" })],
    });

    const { edges } = buildServiceFlowElements(graph, emptyLayout, null);

    // in_journey takes precedence over about — the narrative anchors to the
    // journey, not the persona.
    expect(edges.find((e) => e.id === "in-journey-crossover")).toBeDefined();
    expect(edges.find((e) => e.id.startsWith("about-crossover-"))).toBeUndefined();
  });
});

describe("buildServiceFlowElements — proposes signal", () => {
  it("does not emit edges to Concepts (Concepts live on a different canvas)", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      narratives: [mkNarrative("seed", { proposes: ["new-concept"] })],
    });

    const { edges } = buildServiceFlowElements(graph, emptyLayout, null);

    // proposes is metadata surfaced inside the narrative card label, NOT a
    // canvas edge — the Service canvas does not render Concept nodes.
    expect(edges.find((e) => String(e.target).startsWith("concept:"))).toBeUndefined();
  });
});
