import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SidePanel } from "../src/SidePanel";
import type {
  Concept,
  Graph,
  Identity,
  Journey,
  Layout,
  Narrative,
  Persona,
} from "../src/types";

// Stub `MarkdownBody` so tests don't need the markdown pipeline (and so we
// can grep for raw section content easily).
vi.mock("../src/MarkdownBody", () => ({
  MarkdownBody: ({ text }: { text: string }) => (
    <div data-testid="markdown-body">{text}</div>
  ),
}));

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

const mkPersona = (id: string, overrides: Partial<Persona> = {}): Persona => ({
  id,
  name: id.replace(/-/g, " "),
  status: "active",
  role: "customer",
  identity: `${id} identity paragraph.`,
  goals: [`${id} goal A`, `${id} goal B`],
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
  trigger: `${id} trigger sentence.`,
  steps: [],
  outcome: `${id} outcome sentence.`,
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
  acceptance_cues: [`cue 1 for ${id}`, `cue 2 for ${id}`],
  about_roles: ["customer"],
  about_personas: [],
  in_journey: null,
  proposes: [],
  integrity: [],
  ...overrides,
});

const mkConcept = (id: string, overrides: Partial<Concept> = {}): Concept => ({
  id,
  name: id.replace(/-/g, " "),
  status: "active",
  intent: `Intent for ${id}.`,
  current_design: "",
  current_shape: "",
  horizon: null,
  parent: null,
  ...overrides,
});

const baseProps = {
  projectPath: "/proj",
  layout: { nodes: {} } as Layout,
  onClose: vi.fn(),
  onMutated: vi.fn(),
  onLayoutChange: vi.fn(),
};

beforeEach(() => {
  vi.restoreAllMocks();
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ ok: true, concept_id: "stub", needs_intent_review: true }),
      } as unknown as Response),
    ),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("SidePanel — null selection", () => {
  it("renders nothing when selection is null", () => {
    const { container } = render(
      <SidePanel graph={baseGraph()} selection={null} {...baseProps} />,
    );

    expect(container).toBeEmptyDOMElement();
  });
});

describe("SidePanel — PersonaBody", () => {
  it("renders the persona's name, identity, and goals", () => {
    const graph = baseGraph({ personas: [mkPersona("alice")] });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "persona", id: "alice" }}
        {...baseProps}
      />,
    );

    expect(screen.getByRole("heading", { name: /alice/i })).toBeInTheDocument();
    expect(screen.getByText(/alice identity paragraph/i)).toBeInTheDocument();
    expect(screen.getByText(/alice goal A/)).toBeInTheDocument();
    expect(screen.getByText(/alice goal B/)).toBeInTheDocument();
  });

  it("shows 'Persona not found.' when the id doesn't resolve", () => {
    render(
      <SidePanel
        graph={baseGraph()}
        selection={{ kind: "persona", id: "ghost" }}
        {...baseProps}
      />,
    );

    expect(screen.getByText("Persona not found.")).toBeInTheDocument();
  });

  it("lists journeys that explicitly walk the persona via walked_by", () => {
    // v5.0: Journey.walks references a Role; Personas only see Journeys
    // that named them on `walked_by` (concrete archetype cases).
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      journeys: [
        mkJourney("first-purchase", "customer", { walked_by: ["alice"] }),
      ],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "persona", id: "alice" }}
        {...baseProps}
      />,
    );

    expect(screen.getByText(/first purchase/)).toBeInTheDocument();
  });
});

describe("SidePanel — JourneyBody", () => {
  it("renders trigger, outcome, and walks-Persona name", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      journeys: [mkJourney("first-purchase", "alice")],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "journey", id: "first-purchase" }}
        {...baseProps}
      />,
    );

    expect(screen.getByText(/first-purchase trigger sentence/i)).toBeInTheDocument();
    expect(screen.getByText(/first-purchase outcome sentence/i)).toBeInTheDocument();
    // walks Persona's display name appears in the Walks MetaRow.
    expect(screen.getByText(/alice/i)).toBeInTheDocument();
  });

  it("flags an integrity issue when walks Persona doesn't exist", () => {
    const graph = baseGraph({
      // No personas; journey walks a ghost.
      journeys: [mkJourney("ghost-walk", "missing-persona")],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "journey", id: "ghost-walk" }}
        {...baseProps}
      />,
    );

    // Header chip announces the integrity problem at a glance.
    expect(screen.getByText(/integrity/i)).toBeInTheDocument();
    // IntegrityBanner surfaces the concrete repair target — the missing
    // Persona id — so the human knows exactly what to draw.
    expect(screen.getAllByText(/missing-persona/).length).toBeGreaterThan(0);
  });

  it("surfaces an integrity banner when the walks field is absent", () => {
    const graph = baseGraph({
      // `walks` omitted entirely — Python parser flags this as `missing_walks`.
      journeys: [mkJourney("adrift", "", { walks: "", integrity: ["missing_walks"] })],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "journey", id: "adrift" }}
        {...baseProps}
      />,
    );

    expect(screen.getByText(/integrity/i)).toBeInTheDocument();
    expect(screen.getByText(/no Persona/i)).toBeInTheDocument();
  });

  it("renders steps in order with stage / touchpoint / emotion / pain", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      journeys: [
        mkJourney("first-purchase", "alice", {
          steps: [
            { n: 1, stage: "Discovery", step: "Search", touchpoint: "Web", emotion: "😀", pain: "—" },
            { n: 2, stage: "Signup", step: "Register", touchpoint: "Mobile", emotion: "😐", pain: "Slow email" },
          ],
        }),
      ],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "journey", id: "first-purchase" }}
        {...baseProps}
      />,
    );

    expect(screen.getByText("Search")).toBeInTheDocument();
    expect(screen.getByText("Register")).toBeInTheDocument();
    expect(screen.getByText(/Slow email/)).toBeInTheDocument();
    expect(screen.getByText(/#01/)).toBeInTheDocument();
    expect(screen.getByText(/#02/)).toBeInTheDocument();
  });

  it("shows 'no steps yet' when steps array is empty", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      journeys: [mkJourney("first-purchase", "alice")],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "journey", id: "first-purchase" }}
        {...baseProps}
      />,
    );

    expect(screen.getByText(/no steps yet/i)).toBeInTheDocument();
  });
});

describe("SidePanel — NarrativeBody", () => {
  it("renders statement, context, acceptance cues, and form chip", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      narratives: [mkNarrative("rush-orders")],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "narrative", id: "rush-orders" }}
        {...baseProps}
      />,
    );

    expect(screen.getByText(/As a user, I want rush-orders/)).toBeInTheDocument();
    expect(screen.getByText(/Context for rush-orders/)).toBeInTheDocument();
    expect(screen.getByText("cue 1 for rush-orders")).toBeInTheDocument();
    // Form chip ("user story" with underscore replaced).
    expect(screen.getByText(/user story/)).toBeInTheDocument();
  });

  it("lists Personas the narrative is about (resolved by name)", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      narratives: [mkNarrative("for-alice", { about: ["alice"] })],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "narrative", id: "for-alice" }}
        {...baseProps}
      />,
    );

    // about list resolves to the Persona's display name.
    const aboutRows = screen.getAllByText(/alice/i);
    expect(aboutRows.length).toBeGreaterThan(0);
  });

  it("flags proposed Concepts that still need Intent review", () => {
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      concepts: [
        mkConcept("order-tracking", {
          intent:
            "(proposed from narrative rush on 2026-04-19 — needs human review per solera-write-concept Moment 1 rule)",
        }),
      ],
      narratives: [
        mkNarrative("rush", { proposes: ["order-tracking"] }),
      ],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "narrative", id: "rush" }}
        {...baseProps}
      />,
    );

    expect(screen.getByText(/intent needs review/i)).toBeInTheDocument();
  });
});

describe("SidePanel — ProposeAsConcept modal", () => {
  it("opens the form when the button is clicked", async () => {
    const user = userEvent.setup();
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      narratives: [mkNarrative("rush-orders")],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "narrative", id: "rush-orders" }}
        {...baseProps}
      />,
    );

    await user.click(screen.getByRole("button", { name: /propose as concept/i }));

    // The modal label is unique enough to grep.
    expect(screen.getByText(/Concept ID \(kebab-case\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Concept Name \(human-readable\)/i)).toBeInTheDocument();
  });

  it("loudly explains that the new Concept will need human Intent review", async () => {
    const user = userEvent.setup();
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      narratives: [mkNarrative("rush-orders")],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "narrative", id: "rush-orders" }}
        {...baseProps}
      />,
    );

    await user.click(screen.getByRole("button", { name: /propose as concept/i }));

    // Moment 1 guardrail is surfaced in plain English. "stub Concept" appears
    // in both the modal description and the submit button label — assert at
    // least one match instead of expecting uniqueness.
    expect(screen.getAllByText(/stub Concept/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/needs human review/i)).toBeInTheDocument();
  });

  it("disables the submit button when concept_id is empty", async () => {
    const user = userEvent.setup();
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      narratives: [mkNarrative("rush-orders")],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "narrative", id: "rush-orders" }}
        {...baseProps}
      />,
    );

    await user.click(screen.getByRole("button", { name: /propose as concept/i }));

    const idInput = screen.getByDisplayValue(/rush-orders/);
    await user.clear(idInput);

    const submit = screen.getByRole("button", { name: /create stub concept/i });
    expect(submit).toBeDisabled();
  });

  it("submits a POST and calls onMutated on success", async () => {
    const user = userEvent.setup();
    const onMutated = vi.fn();
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      narratives: [mkNarrative("rush-orders")],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "narrative", id: "rush-orders" }}
        {...baseProps}
        onMutated={onMutated}
      />,
    );

    await user.click(screen.getByRole("button", { name: /propose as concept/i }));
    await user.click(screen.getByRole("button", { name: /create stub concept/i }));

    await waitFor(() => expect(onMutated).toHaveBeenCalledOnce());

    expect(globalThis.fetch).toHaveBeenCalledOnce();
    const callArgs = vi.mocked(globalThis.fetch).mock.calls[0];
    expect(String(callArgs[0])).toContain("propose-from-narrative");
    expect(callArgs[1]?.method).toBe("POST");
    const body = JSON.parse(callArgs[1]?.body as string);
    expect(body).toEqual({
      narrative_id: "rush-orders",
      concept_id: "rush-orders",
      concept_name: "Rush Orders",
    });
  });

  it("displays server error when POST fails", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 409,
          json: () => Promise.resolve({ error: "Concept already exists" }),
        } as unknown as Response),
      ),
    );

    const graph = baseGraph({
      personas: [mkPersona("alice")],
      narratives: [mkNarrative("rush-orders")],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "narrative", id: "rush-orders" }}
        {...baseProps}
      />,
    );

    await user.click(screen.getByRole("button", { name: /propose as concept/i }));
    await user.click(screen.getByRole("button", { name: /create stub concept/i }));

    expect(await screen.findByText(/Concept already exists/i)).toBeInTheDocument();
  });

  it("cancels the form without submitting", async () => {
    const user = userEvent.setup();
    const onMutated = vi.fn();
    const graph = baseGraph({
      personas: [mkPersona("alice")],
      narratives: [mkNarrative("rush-orders")],
    });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "narrative", id: "rush-orders" }}
        {...baseProps}
        onMutated={onMutated}
      />,
    );

    await user.click(screen.getByRole("button", { name: /propose as concept/i }));
    await user.click(screen.getByRole("button", { name: /^cancel$/i }));

    expect(globalThis.fetch).not.toHaveBeenCalled();
    expect(onMutated).not.toHaveBeenCalled();
    // The "Propose as Concept" button is back (form collapsed).
    expect(screen.getByRole("button", { name: /propose as concept/i })).toBeInTheDocument();
  });
});

describe("SidePanel — Close button", () => {
  it("invokes onClose when the close button is clicked", () => {
    const onClose = vi.fn();
    const graph = baseGraph({ personas: [mkPersona("alice")] });

    render(
      <SidePanel
        graph={graph}
        selection={{ kind: "persona", id: "alice" }}
        {...baseProps}
        onClose={onClose}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: /close panel/i }));

    expect(onClose).toHaveBeenCalledOnce();
  });
});
