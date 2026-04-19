// Wire types that mirror `solera_map.graph` (by_alias JSON output).

export type ConceptStatus = "active" | "deprecated" | "archived";
export type MilestoneStatus = "proposed" | "agreed" | "in-progress" | "released";
export type WorkStatus = "pending" | "in_progress" | "complete" | "on_hold" | "cancelled";
export type NarrativeForm = "user_story" | "jtbd" | "scenario";

export interface Concept {
  id: string;
  name: string;
  status: ConceptStatus;
  intent: string;
  current_design: string;
  current_shape: string;
  horizon: string | null;
  parent: string | null;
}

// v4 Living-axis additions — upstream of Concept.

export interface Role {
  id: string;
  name: string;
  status: ConceptStatus;
  description: string;
  context: string | null;
  parent: string | null;
  integrity: string[];
}

export interface Persona {
  id: string;
  name: string;
  status: ConceptStatus;
  role: string; // v5.0+ required: Role id this Persona archetypes
  identity: string;
  goals: string[];
  pains: string[];
  triggers: string[];
  quotes: string[];
  channels: string | null;
  parent: string | null;
  integrity: string[];
}

export interface JourneyStep {
  n: number;
  stage: string;
  step: string;
  touchpoint: string;
  emotion: string;
  pain: string;
}

export interface Journey {
  id: string;
  name: string;
  status: ConceptStatus;
  walks: string; // v5.0+: Role id, "" when orphan
  walked_by: string[]; // optional Persona ids for concrete cases
  trigger: string;
  steps: JourneyStep[];
  outcome: string;
  parent: string | null;
  // Data-integrity flags from the MCP parser: e.g. `missing_walks`,
  // `broken_walks_ref`. Canvas and SidePanel surface these so the human can
  // repair the underlying file.
  integrity: string[];
}

export interface Narrative {
  id: string;
  form: NarrativeForm;
  status: ConceptStatus;
  statement: string;
  context: string;
  acceptance_cues: string[];
  about_roles: string[]; // v5.0+: 1+ required (Role ids)
  about_personas: string[]; // v5.0+: optional (Persona ids)
  in_journey: string | null;
  proposes: string[];
  // Data-integrity flags from the MCP parser: e.g. `missing_about_roles`,
  // `broken_about_role_ref`, `legacy_about_field`, `broken_in_journey_ref`.
  integrity: string[];
}

export interface ConceptEdge {
  id: string;
  from: string; // aliased from from_id
  to: string; // aliased from to_id
  label: string;
  created: string | null;
}

export interface Story {
  id: string;
  name: string;
  story_type: string;
  status: WorkStatus;
  contributes_to: string[];
  belongs_to: string | null;
}

export interface ActionItem {
  story_id: string;
  id: string;
  name: string;
  status: WorkStatus;
  depends_on: string[];
}

export interface Milestone {
  id: string;
  name: string;
  status: MilestoneStatus;
  scope: string[];
}

export interface Identity {
  mission: string | null;
  vision: string | null;
  values: string | null;
  goals: string | null;
  tone_and_manner: string | null;
  extras: Record<string, string>;
}

export interface Release {
  tag: string;
  milestone_id: string | null;
  released_at: string | null;
}

export interface Graph {
  identity: Identity | null;
  roles: Role[];
  personas: Persona[];
  journeys: Journey[];
  narratives: Narrative[];
  concepts: Concept[];
  concept_edges: ConceptEdge[];
  milestones: Milestone[];
  stories: Story[];
  action_items: ActionItem[];
  releases: Release[];
}

// `service` is leftmost — it is upstream of Plan in the user's mental model
// (humans draw Personas/Journeys/Narratives, then propose Concepts to Plan).
export type WorkspaceLens = "service" | "plan" | "build" | "live";

export type BranchSide = "left" | "right";

export interface NodeLayout {
  // Persisted drag position. When omitted, the canvas uses auto-layout.
  x?: number;
  y?: number;
  collapsed?: boolean;
  // Only meaningful for top-level Concepts on the Plan canvas. Decides which
  // side of the Identity root this branch and its subtree extends toward.
  side?: BranchSide;
}

export interface Layout {
  nodes: Record<string, NodeLayout>;
}
