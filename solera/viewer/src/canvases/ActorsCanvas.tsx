import { useMemo } from "react";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MarkerType,
  Position,
  type NodeProps,
  type Edge,
  type Node,
  type NodeChange,
  applyNodeChanges,
} from "reactflow";
import type {
  Graph,
  Identity,
  Journey,
  Layout,
  Narrative,
  Persona,
  Role,
} from "../types";
import type { SelectedNode } from "./PlanCanvas";

interface ActorsCanvasProps {
  graph: Graph;
  layout: Layout;
  onLayoutChange: (next: Layout) => void;
  onSelect: (selection: SelectedNode | null) => void;
  selection: SelectedNode | null;
}

// Identity-centric unified Actors mindmap (v5.0):
//
//   - The project's Identity sits at the origin.
//   - Top-level Roles form the first ring around Identity; each Role
//     claims an angular wedge proportional to its subtree size.
//   - Child Roles (`role.parent`) nest outward inside their parent's
//     wedge at a larger radius. Depth is unbounded.
//   - Each Role carries its Journeys (`journey.walks`) on an arc just
//     outside the Role's radius, in the same wedge.
//   - Narratives: anchored to their Journey (`in_journey`) sit one
//     radius beyond the Journey; Narratives that only have
//     `about_roles` hang directly off the Role, in the same wedge.
//   - Personas (concrete archetypes) are small satellite nodes placed
//     just outside their parent Role.
//   - Orphans (broken references, fully-loose Narratives) get
//     dedicated rows below the mindmap so the integrity banners in the
//     SidePanel remain easy to find.
//
// Drag persists via `layout.nodes` and overrides auto-layout on
// subsequent renders.

const ROLE_RADIUS_BASE = 360;
const ROLE_RADIUS_STEP = 280;
const JOURNEY_RADIUS_DELTA = 220;
const NARRATIVE_RADIUS_DELTA = 220;
const PERSONA_SATELLITE_RADIUS_DELTA = 120;
const PERSONA_SATELLITE_OFFSET = 0.18;

const WEDGE_CHILD_SHARE = 0.6;
const JOURNEY_FAN_MAX = Math.PI / 3;
const NARRATIVE_FAN_MAX = Math.PI / 3;

const IDENTITY_NODE_ID = "identity";

const ORPHAN_ROW_GAP = 260;
const ORPHAN_STEP_X = 360;

export function ActorsCanvas({
  graph,
  layout,
  onLayoutChange,
  onSelect,
  selection,
}: ActorsCanvasProps) {
  const { nodes, edges } = useMemo(
    () => buildActorsFlowElements(graph, layout, selection),
    [graph, layout, selection],
  );

  const handleNodesChange = (changes: NodeChange[]) => {
    const positionCommits = changes.filter(
      (c): c is Extract<NodeChange, { type: "position" }> =>
        c.type === "position" && c.dragging === false && c.position !== undefined,
    );
    if (positionCommits.length === 0) return;

    const updated = applyNodeChanges(changes, nodes);
    const nextNodes = { ...layout.nodes };
    for (const node of updated) {
      const prior = layout.nodes[node.id];
      nextNodes[node.id] = {
        ...(prior ?? {}),
        x: node.position.x,
        y: node.position.y,
      };
    }
    onLayoutChange({ ...layout, nodes: nextNodes });
  };

  if (
    graph.roles.length === 0 &&
    graph.personas.length === 0 &&
    graph.journeys.length === 0 &&
    graph.narratives.length === 0
  ) {
    return (
      <div className="flex h-full items-center justify-center px-8 text-center text-slate-500">
        <div className="max-w-md">
          <h2 className="mb-2 text-xl font-semibold text-slate-700">
            No Actors yet
          </h2>
          <p className="text-sm">
            The Actors canvas renders <strong>Roles</strong> (admin, fan, hero,
            3rd-party, …), their optional <strong>Personas</strong>,{" "}
            <strong>Journeys</strong>, and <strong>Narratives</strong>, all
            radiating from the project's Identity. Run{" "}
            <code>solera-write-role</code> to draw your first structural
            audience class.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        nodesDraggable
        nodesConnectable={false}
        elementsSelectable
        onNodesChange={handleNodesChange}
        onNodeClick={(_evt, node) => {
          if (node.id === IDENTITY_NODE_ID) {
            onSelect({ kind: "identity", id: IDENTITY_NODE_ID });
          } else if (node.id.startsWith("role:")) {
            onSelect({ kind: "role", id: node.id.slice("role:".length) });
          } else if (node.id.startsWith("persona:")) {
            onSelect({ kind: "persona", id: node.id.slice("persona:".length) });
          } else if (node.id.startsWith("journey:")) {
            onSelect({ kind: "journey", id: node.id.slice("journey:".length) });
          } else if (node.id.startsWith("narrative:")) {
            onSelect({ kind: "narrative", id: node.id.slice("narrative:".length) });
          }
        }}
        onPaneClick={() => onSelect(null)}
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#fce7f3" />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

export function buildActorsFlowElements(
  graph: Graph,
  layout: Layout,
  selection: SelectedNode | null,
): { nodes: Node[]; edges: Edge[] } {
  const roles = graph.roles;
  const roleIdSet = new Set(roles.map((r) => r.id));
  const journeyIdSet = new Set(graph.journeys.map((j) => j.id));

  const childrenByParent = new Map<string, Role[]>();
  for (const r of roles) {
    if (!r.parent || !roleIdSet.has(r.parent)) continue;
    const bucket = childrenByParent.get(r.parent) ?? [];
    bucket.push(r);
    childrenByParent.set(r.parent, bucket);
  }
  const topLevelRoles = roles.filter(
    (r) => !r.parent || !roleIdSet.has(r.parent),
  );

  const journeysByRole = new Map<string, Journey[]>();
  for (const j of graph.journeys) {
    if (!j.walks || !roleIdSet.has(j.walks)) continue;
    const bucket = journeysByRole.get(j.walks) ?? [];
    bucket.push(j);
    journeysByRole.set(j.walks, bucket);
  }
  const personasByRole = new Map<string, Persona[]>();
  for (const p of graph.personas) {
    if (!p.role || !roleIdSet.has(p.role)) continue;
    const bucket = personasByRole.get(p.role) ?? [];
    bucket.push(p);
    personasByRole.set(p.role, bucket);
  }
  const narrativesByJourney = new Map<string, Narrative[]>();
  const narrativesByRole = new Map<string, Narrative[]>();
  for (const n of graph.narratives) {
    if (n.in_journey && journeyIdSet.has(n.in_journey)) {
      const bucket = narrativesByJourney.get(n.in_journey) ?? [];
      bucket.push(n);
      narrativesByJourney.set(n.in_journey, bucket);
      continue;
    }
    const anchor = n.about_roles.find((r) => roleIdSet.has(r));
    if (anchor) {
      const bucket = narrativesByRole.get(anchor) ?? [];
      bucket.push(n);
      narrativesByRole.set(anchor, bucket);
    }
  }

  const autoPositions = new Map<string, { x: number; y: number }>();

  const showIdentity = hasIdentityContent(graph.identity);
  if (showIdentity) {
    autoPositions.set(IDENTITY_NODE_ID, { x: 0, y: 0 });
  }

  const topWeights = topLevelRoles.map((r) =>
    computeSubtreeWeight(
      r,
      childrenByParent,
      journeysByRole,
      personasByRole,
      narrativesByRole,
      narrativesByJourney,
    ),
  );
  const totalWeight = topWeights.reduce((a, b) => a + b, 0) || 1;

  const firstArc = ((topWeights[0] ?? 0) / totalWeight) * 2 * Math.PI;
  let cursorAngle = -Math.PI / 2 - firstArc / 2;
  topLevelRoles.forEach((role, i) => {
    const arc = (topWeights[i] / totalWeight) * 2 * Math.PI;
    const centerAngle = cursorAngle + arc / 2;
    placeRoleSubtree(
      role,
      1,
      centerAngle,
      arc,
      childrenByParent,
      journeysByRole,
      personasByRole,
      narrativesByRole,
      narrativesByJourney,
      autoPositions,
    );
    cursorAngle += arc;
  });

  // Orphan rows: one row per kind so the banners group naturally.
  const orphanRoles = roles.filter(
    (r) => r.parent && !roleIdSet.has(r.parent),
  );
  const orphanPersonas = graph.personas.filter(
    (p) => !p.role || !roleIdSet.has(p.role),
  );
  const orphanJourneys = graph.journeys.filter(
    (j) => !j.walks || !roleIdSet.has(j.walks),
  );
  const orphanNarratives = graph.narratives.filter((n) => {
    const resolvedJourney = n.in_journey && journeyIdSet.has(n.in_journey);
    const resolvedRoleAbout = n.about_roles.some((r) => roleIdSet.has(r));
    return !resolvedJourney && !resolvedRoleAbout;
  });
  const hasOrphans =
    orphanRoles.length > 0 ||
    orphanPersonas.length > 0 ||
    orphanJourneys.length > 0 ||
    orphanNarratives.length > 0;
  if (hasOrphans) {
    const outermost =
      ROLE_RADIUS_BASE +
      ROLE_RADIUS_STEP *
        Math.max(1, computeMaxDepth(topLevelRoles, childrenByParent) - 1) +
      JOURNEY_RADIUS_DELTA +
      NARRATIVE_RADIUS_DELTA;
    const baseY = outermost + ORPHAN_ROW_GAP;
    orphanRoles.forEach((r, i) =>
      autoPositions.set(`role:${r.id}`, { x: i * ORPHAN_STEP_X, y: baseY }),
    );
    orphanPersonas.forEach((p, i) =>
      autoPositions.set(`persona:${p.id}`, {
        x: i * ORPHAN_STEP_X,
        y: baseY + ORPHAN_ROW_GAP,
      }),
    );
    orphanJourneys.forEach((j, i) =>
      autoPositions.set(`journey:${j.id}`, {
        x: i * ORPHAN_STEP_X,
        y: baseY + ORPHAN_ROW_GAP * 2,
      }),
    );
    orphanNarratives.forEach((n, i) =>
      autoPositions.set(`narrative:${n.id}`, {
        x: i * ORPHAN_STEP_X,
        y: baseY + ORPHAN_ROW_GAP * 3,
      }),
    );
  }

  const positionOf = (id: string, fallback: { x: number; y: number }) => {
    const stored = layout.nodes[id];
    if (stored?.x !== undefined && stored?.y !== undefined) {
      return { x: stored.x, y: stored.y };
    }
    return fallback;
  };

  const nodes: Node[] = [];

  if (showIdentity && graph.identity) {
    const isSelected = selection?.kind === "identity";
    nodes.push({
      id: IDENTITY_NODE_ID,
      type: "identity",
      position: positionOf(IDENTITY_NODE_ID, autoPositions.get(IDENTITY_NODE_ID) ?? { x: 0, y: 0 }),
      data: { children: renderIdentityLabel(graph.identity) },
      style: {
        background: "#0f172a",
        color: "white",
        border: `${isSelected ? 3 : 2}px solid ${isSelected ? "#fbbf24" : "#0f172a"}`,
        borderRadius: 18,
        padding: "14px 22px",
        minWidth: 200,
        maxWidth: 280,
        cursor: "pointer",
      },
    });
  }

  for (const role of roles) {
    const id = `role:${role.id}`;
    const isSelected = selection?.kind === "role" && selection.id === role.id;
    const hasIntegrityIssue = role.integrity.length > 0;
    nodes.push({
      id,
      position: positionOf(id, autoPositions.get(id) ?? { x: 0, y: 0 }),
      data: { label: renderRoleLabel(role) },
      style: {
        background: hasIntegrityIssue
          ? "#fef2f2"
          : role.status === "deprecated"
            ? "#fef3c7"
            : "#fdf2f8",
        border: `${isSelected || hasIntegrityIssue ? 3 : 2}px solid ${
          isSelected ? "#6366f1" : hasIntegrityIssue ? "#ef4444" : "#f9a8d4"
        }`,
        borderRadius: 14,
        padding: "12px 16px",
        minWidth: 240,
        maxWidth: 300,
        cursor: "pointer",
      },
    });
  }

  for (const persona of graph.personas) {
    const id = `persona:${persona.id}`;
    const isSelected =
      selection?.kind === "persona" && selection.id === persona.id;
    const hasIntegrityIssue = persona.integrity.length > 0;
    nodes.push({
      id,
      position: positionOf(id, autoPositions.get(id) ?? { x: 0, y: 0 }),
      data: { label: renderPersonaLabel(persona) },
      style: {
        background: hasIntegrityIssue
          ? "#fef2f2"
          : persona.status === "deprecated"
            ? "#fef3c7"
            : "#fff7ed",
        border: `${isSelected || hasIntegrityIssue ? 3 : 2}px solid ${
          isSelected ? "#6366f1" : hasIntegrityIssue ? "#ef4444" : "#fdba74"
        }`,
        borderRadius: 12,
        padding: "8px 12px",
        minWidth: 200,
        maxWidth: 260,
        cursor: "pointer",
      },
    });
  }

  for (const journey of graph.journeys) {
    const id = `journey:${journey.id}`;
    const isSelected = selection?.kind === "journey" && selection.id === journey.id;
    const orphan = !journey.walks || !roleIdSet.has(journey.walks);
    const hasIntegrityIssue = journey.integrity.length > 0 || orphan;
    nodes.push({
      id,
      position: positionOf(id, autoPositions.get(id) ?? { x: 0, y: 0 }),
      data: { label: renderJourneyLabel(journey, orphan) },
      style: {
        background: hasIntegrityIssue
          ? "#fef2f2"
          : journey.status === "deprecated"
            ? "#fef3c7"
            : "#eff6ff",
        border: `${isSelected || hasIntegrityIssue ? 3 : 2}px solid ${
          isSelected ? "#6366f1" : hasIntegrityIssue ? "#ef4444" : "#93c5fd"
        }`,
        borderRadius: 12,
        padding: "10px 14px",
        minWidth: 260,
        maxWidth: 320,
        cursor: "pointer",
      },
    });
  }

  for (const narrative of graph.narratives) {
    const id = `narrative:${narrative.id}`;
    const isSelected =
      selection?.kind === "narrative" && selection.id === narrative.id;
    const hasIntegrityIssue = narrative.integrity.length > 0;
    nodes.push({
      id,
      position: positionOf(id, autoPositions.get(id) ?? { x: 0, y: 0 }),
      data: { label: renderNarrativeLabel(narrative) },
      style: {
        background: hasIntegrityIssue
          ? "#fef2f2"
          : narrative.status === "deprecated"
            ? "#fef3c7"
            : "#f0fdf4",
        border: `${isSelected || hasIntegrityIssue ? 3 : 2}px solid ${
          isSelected
            ? "#6366f1"
            : hasIntegrityIssue
              ? "#ef4444"
              : narrative.proposes.length > 0
                ? "#86efac"
                : "#bbf7d0"
        }`,
        borderRadius: 12,
        padding: "10px 14px",
        minWidth: 240,
        maxWidth: 300,
        cursor: "pointer",
      },
    });
  }

  const edges: Edge[] = [];

  if (showIdentity) {
    for (const top of topLevelRoles) {
      edges.push({
        id: `identity-${top.id}`,
        source: IDENTITY_NODE_ID,
        target: `role:${top.id}`,
        style: { stroke: "#cbd5e1", strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: "#cbd5e1" },
      });
    }
  }

  for (const role of roles) {
    if (!role.parent || !roleIdSet.has(role.parent)) continue;
    edges.push({
      id: `parent-role-${role.id}`,
      source: `role:${role.parent}`,
      target: `role:${role.id}`,
      style: { stroke: "#cbd5e1", strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#cbd5e1" },
    });
  }

  for (const persona of graph.personas) {
    if (!persona.role || !roleIdSet.has(persona.role)) continue;
    edges.push({
      id: `role-persona-${persona.id}`,
      source: `role:${persona.role}`,
      target: `persona:${persona.id}`,
      label: "archetype",
      labelStyle: { fontSize: 10, fill: "#ea580c" },
      style: { stroke: "#fdba74", strokeDasharray: "3 2" },
    });
  }

  for (const journey of graph.journeys) {
    if (!journey.walks || !roleIdSet.has(journey.walks)) continue;
    edges.push({
      id: `walks-${journey.id}`,
      source: `role:${journey.walks}`,
      target: `journey:${journey.id}`,
      label: "walks",
      labelStyle: { fontSize: 10, fill: "#7c3aed" },
      style: { stroke: "#c4b5fd", strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#c4b5fd" },
    });
  }

  for (const journey of graph.journeys) {
    for (const personaId of journey.walked_by) {
      edges.push({
        id: `walked-by-${journey.id}-${personaId}`,
        source: `journey:${journey.id}`,
        target: `persona:${personaId}`,
        style: { stroke: "#e2e8f0", strokeDasharray: "2 3" },
      });
    }
  }

  for (const narrative of graph.narratives) {
    if (narrative.in_journey && journeyIdSet.has(narrative.in_journey)) {
      edges.push({
        id: `in-journey-${narrative.id}`,
        source: `journey:${narrative.in_journey}`,
        target: `narrative:${narrative.id}`,
        style: { stroke: "#94a3b8", strokeDasharray: "4 3" },
      });
    } else {
      const anchor = narrative.about_roles.find((r) => roleIdSet.has(r));
      if (anchor) {
        edges.push({
          id: `about-role-${narrative.id}-${anchor}`,
          source: `role:${anchor}`,
          target: `narrative:${narrative.id}`,
          style: { stroke: "#cbd5e1", strokeDasharray: "2 4" },
        });
      }
    }
  }

  return { nodes, edges };
}

// ---------------------------------------------------------------------------
// Identity node
// ---------------------------------------------------------------------------

function IdentityNodeView({ data }: NodeProps<{ children: React.ReactNode }>) {
  return (
    <>
      <Handle type="source" position={Position.Left} id="left" style={HANDLE_STYLE} />
      <Handle type="source" position={Position.Right} id="right" style={HANDLE_STYLE} />
      <Handle type="source" position={Position.Top} id="top" style={HANDLE_STYLE} />
      <Handle type="source" position={Position.Bottom} id="bottom" style={HANDLE_STYLE} />
      {data.children}
    </>
  );
}

const NODE_TYPES = { identity: IdentityNodeView };

const HANDLE_STYLE: React.CSSProperties = {
  width: 6,
  height: 6,
  background: "#1e293b",
  border: "1px solid #0f172a",
};

function renderIdentityLabel(identity: Identity): React.ReactNode {
  const first = firstMeaningfulLine(
    identity.mission ?? identity.vision ?? identity.values ?? "",
  );
  return (
    <div className="text-left">
      <div className="text-[10px] font-semibold uppercase tracking-widest text-amber-300">
        identity
      </div>
      {first && (
        <div className="mt-1 text-[12px] leading-tight text-slate-200 line-clamp-3">
          {first}
        </div>
      )}
    </div>
  );
}

function firstMeaningfulLine(text: string): string {
  for (const raw of text.split("\n")) {
    const trimmed = raw.trim();
    if (!trimmed) continue;
    if (trimmed.startsWith("#")) continue;
    if (trimmed.startsWith("<!--")) continue;
    return trimmed.replace(/^>\s*/, "").replace(/\*\*/g, "").trim();
  }
  return "";
}

function hasIdentityContent(identity: Identity | null): boolean {
  if (!identity) return false;
  if (identity.mission) return true;
  if (identity.vision) return true;
  if (identity.values) return true;
  if (identity.goals) return true;
  if (identity.tone_and_manner) return true;
  if (Object.keys(identity.extras ?? {}).length > 0) return true;
  return false;
}

// ---------------------------------------------------------------------------
// Role subtree placement
// ---------------------------------------------------------------------------

function computeSubtreeWeight(
  role: Role,
  childrenByParent: Map<string, Role[]>,
  journeysByRole: Map<string, Journey[]>,
  personasByRole: Map<string, Persona[]>,
  narrativesByRole: Map<string, Narrative[]>,
  narrativesByJourney: Map<string, Narrative[]>,
): number {
  const ownJourneys = journeysByRole.get(role.id) ?? [];
  const ownPersonas = personasByRole.get(role.id) ?? [];
  const ownNarratives = narrativesByRole.get(role.id) ?? [];
  const narrativesFromJourneys = ownJourneys.reduce(
    (acc, j) => acc + (narrativesByJourney.get(j.id)?.length ?? 0),
    0,
  );
  const selfWeight =
    1 +
    ownJourneys.length * 0.6 +
    ownNarratives.length * 0.4 +
    narrativesFromJourneys * 0.3 +
    ownPersonas.length * 0.5;
  const children = childrenByParent.get(role.id) ?? [];
  const childWeight = children.reduce(
    (acc, c) =>
      acc +
      computeSubtreeWeight(
        c,
        childrenByParent,
        journeysByRole,
        personasByRole,
        narrativesByRole,
        narrativesByJourney,
      ),
    0,
  );
  return selfWeight + childWeight;
}

function computeMaxDepth(
  tops: Role[],
  childrenByParent: Map<string, Role[]>,
): number {
  let maxDepth = 1;
  const visit = (r: Role, depth: number) => {
    maxDepth = Math.max(maxDepth, depth);
    for (const child of childrenByParent.get(r.id) ?? []) visit(child, depth + 1);
  };
  for (const t of tops) visit(t, 1);
  return maxDepth;
}

function placeRoleSubtree(
  role: Role,
  depth: number,
  centerAngle: number,
  arc: number,
  childrenByParent: Map<string, Role[]>,
  journeysByRole: Map<string, Journey[]>,
  personasByRole: Map<string, Persona[]>,
  narrativesByRole: Map<string, Narrative[]>,
  narrativesByJourney: Map<string, Narrative[]>,
  positions: Map<string, { x: number; y: number }>,
): void {
  const roleRadius = ROLE_RADIUS_BASE + (depth - 1) * ROLE_RADIUS_STEP;
  positions.set(`role:${role.id}`, {
    x: roleRadius * Math.cos(centerAngle),
    y: roleRadius * Math.sin(centerAngle),
  });

  const children = childrenByParent.get(role.id) ?? [];
  const ownJourneys = journeysByRole.get(role.id) ?? [];
  const ownPersonas = personasByRole.get(role.id) ?? [];
  const looseNarratives = narrativesByRole.get(role.id) ?? [];

  ownPersonas.forEach((p, i) => {
    const sign = i % 2 === 0 ? 1 : -1;
    const offset = sign * PERSONA_SATELLITE_OFFSET * Math.ceil((i + 1) / 2);
    const pAngle = centerAngle + offset;
    const pRadius = roleRadius + PERSONA_SATELLITE_RADIUS_DELTA;
    positions.set(`persona:${p.id}`, {
      x: pRadius * Math.cos(pAngle),
      y: pRadius * Math.sin(pAngle),
    });
  });

  const hasChildren = children.length > 0;
  const hasLeaves = ownJourneys.length > 0 || looseNarratives.length > 0;
  const childArcShare = hasChildren && hasLeaves ? WEDGE_CHILD_SHARE : hasChildren ? 1 : 0;

  if (hasChildren) {
    const childArcTotal = arc * childArcShare;
    const childWeights = children.map((c) =>
      computeSubtreeWeight(
        c,
        childrenByParent,
        journeysByRole,
        personasByRole,
        narrativesByRole,
        narrativesByJourney,
      ),
    );
    const totalCW = childWeights.reduce((a, b) => a + b, 0) || 1;
    let cursor = centerAngle - childArcTotal / 2;
    children.forEach((child, i) => {
      const childArc = (childWeights[i] / totalCW) * childArcTotal;
      placeRoleSubtree(
        child,
        depth + 1,
        cursor + childArc / 2,
        childArc,
        childrenByParent,
        journeysByRole,
        personasByRole,
        narrativesByRole,
        narrativesByJourney,
        positions,
      );
      cursor += childArc;
    });
  }

  const journeyRadius = roleRadius + JOURNEY_RADIUS_DELTA;
  const journeyArc = journeyFanWidth(ownJourneys, arc * (1 - childArcShare));
  const journeyAngles = new Map<string, number>();
  if (ownJourneys.length > 0) {
    ownJourneys.forEach((j, i) => {
      const offset =
        ownJourneys.length === 1
          ? 0
          : -journeyArc / 2 + (i / (ownJourneys.length - 1)) * journeyArc;
      const angle = centerAngle + offset;
      journeyAngles.set(j.id, angle);
      positions.set(`journey:${j.id}`, {
        x: journeyRadius * Math.cos(angle),
        y: journeyRadius * Math.sin(angle),
      });

      const anchoredNars = narrativesByJourney.get(j.id) ?? [];
      if (anchoredNars.length === 0) return;
      const narrativeRadius = journeyRadius + NARRATIVE_RADIUS_DELTA;
      const narrativeArc = Math.min(
        NARRATIVE_FAN_MAX,
        (journeyArc / Math.max(ownJourneys.length, 1)) * 0.8,
      );
      anchoredNars.forEach((n, k) => {
        const nOffset =
          anchoredNars.length === 1
            ? 0
            : -narrativeArc / 2 + (k / (anchoredNars.length - 1)) * narrativeArc;
        const nAngle = angle + nOffset;
        positions.set(`narrative:${n.id}`, {
          x: narrativeRadius * Math.cos(nAngle),
          y: narrativeRadius * Math.sin(nAngle),
        });
      });
    });
  }

  if (looseNarratives.length > 0) {
    const looseRadius = roleRadius + JOURNEY_RADIUS_DELTA;
    const looseArcBand = arc * (1 - childArcShare);
    looseNarratives.forEach((n, i) => {
      const offset =
        looseNarratives.length === 1
          ? looseArcBand / 2 + 0.12
          : -looseArcBand / 2 + (i / (looseNarratives.length - 1)) * looseArcBand;
      const angle = centerAngle + offset;
      positions.set(`narrative:${n.id}`, {
        x: looseRadius * Math.cos(angle),
        y: looseRadius * Math.sin(angle),
      });
    });
  }
}

function journeyFanWidth(journeys: Journey[], availableArc: number): number {
  if (journeys.length === 0) return 0;
  if (journeys.length === 1) return 0;
  const natural = Math.min(JOURNEY_FAN_MAX, (journeys.length - 1) * 0.3);
  return Math.min(natural, Math.max(availableArc * 0.85, 0.3));
}

// ---------------------------------------------------------------------------
// Label renderers
// ---------------------------------------------------------------------------

function renderRoleLabel(role: Role): React.ReactNode {
  const hasIntegrityIssue = role.integrity.length > 0;
  return (
    <div className="flex flex-col gap-1 text-left">
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wide text-pink-600">Role</span>
        {hasIntegrityIssue && (
          <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700 ring-1 ring-red-300">
            <span aria-hidden>⚠</span>
            <span>{integrityShortLabel(role.integrity, false)}</span>
          </span>
        )}
        {role.status !== "active" && (
          <span className="text-[10px] uppercase tracking-wide text-amber-700">
            {role.status}
          </span>
        )}
      </div>
      <div className="text-base font-semibold text-slate-800">{role.name}</div>
      {role.description && (
        <div className="line-clamp-3 text-xs text-slate-700">{role.description}</div>
      )}
    </div>
  );
}

function renderPersonaLabel(persona: Persona): React.ReactNode {
  const firstSentence = persona.identity.split(/[.!?]\s/)[0]?.trim() ?? "";
  const hasIntegrityIssue = persona.integrity.length > 0;
  return (
    <div className="flex flex-col gap-1 text-left">
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wide text-orange-600">
          Persona
        </span>
        {hasIntegrityIssue && (
          <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700 ring-1 ring-red-300">
            <span aria-hidden>⚠</span>
            <span>{integrityShortLabel(persona.integrity, false)}</span>
          </span>
        )}
        {persona.status !== "active" && (
          <span className="text-[10px] uppercase tracking-wide text-amber-700">
            {persona.status}
          </span>
        )}
      </div>
      <div className="text-sm font-semibold text-slate-800">{persona.name}</div>
      {firstSentence && (
        <div className="line-clamp-2 text-xs text-slate-600">{firstSentence}</div>
      )}
    </div>
  );
}

function renderJourneyLabel(journey: Journey, orphan: boolean): React.ReactNode {
  const hasIntegrityIssue = journey.integrity.length > 0 || orphan;
  return (
    <div className="flex flex-col gap-1 text-left">
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wide text-blue-600">
          Journey
        </span>
        {hasIntegrityIssue && (
          <span
            className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700 ring-1 ring-red-300"
            title={integrityTooltip("journey", journey.integrity, orphan)}
          >
            <span aria-hidden>⚠</span>
            <span>{integrityShortLabel(journey.integrity, orphan)}</span>
          </span>
        )}
        {journey.status !== "active" && (
          <span className="text-[10px] uppercase tracking-wide text-amber-700">
            {journey.status}
          </span>
        )}
      </div>
      <div className="text-base font-semibold text-slate-800">{journey.name}</div>
      {journey.trigger && (
        <div className="line-clamp-2 text-xs text-slate-600">
          <span className="text-slate-400">Trigger: </span>
          {journey.trigger}
        </div>
      )}
      <div className="mt-1 text-[11px] text-slate-500">
        {journey.steps.length} step{journey.steps.length === 1 ? "" : "s"}
        {journey.walks && (
          <span className="text-slate-400"> · walks {journey.walks}</span>
        )}
      </div>
    </div>
  );
}

function renderNarrativeLabel(narrative: Narrative): React.ReactNode {
  const formColor =
    narrative.form === "jtbd"
      ? "text-violet-600"
      : narrative.form === "scenario"
        ? "text-teal-600"
        : "text-emerald-600";
  const hasIntegrityIssue = narrative.integrity.length > 0;
  return (
    <div className="flex flex-col gap-1 text-left">
      <div className="flex items-center gap-2">
        <span className={`text-[10px] uppercase tracking-wide ${formColor}`}>
          {narrative.form.replace("_", " ")}
        </span>
        {hasIntegrityIssue && (
          <span
            className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700 ring-1 ring-red-300"
            title={integrityTooltip("narrative", narrative.integrity, false)}
          >
            <span aria-hidden>⚠</span>
            <span>{integrityShortLabel(narrative.integrity, false)}</span>
          </span>
        )}
        {narrative.status !== "active" && (
          <span className="text-[10px] uppercase tracking-wide text-amber-700">
            {narrative.status}
          </span>
        )}
      </div>
      <div className="text-xs italic leading-snug text-slate-700 line-clamp-3">
        {narrative.statement || <span className="text-slate-400">(no statement)</span>}
      </div>
      {narrative.proposes.length > 0 && (
        <div className="mt-1 text-[11px] text-emerald-700">
          → proposes {narrative.proposes.length} Concept
          {narrative.proposes.length === 1 ? "" : "s"}
        </div>
      )}
    </div>
  );
}

function integrityShortLabel(flags: string[], orphan: boolean): string {
  if (flags.includes("missing_role")) return "no role";
  if (flags.includes("broken_role_ref")) return "unknown role";
  if (flags.includes("missing_walks")) return "no walks";
  if (flags.includes("broken_walks_ref")) return "unknown role (walks)";
  if (flags.includes("missing_about_roles")) return "no roles";
  if (flags.includes("broken_about_role_ref")) return "unknown role";
  if (flags.includes("broken_about_persona_ref")) return "unknown persona";
  if (flags.includes("broken_in_journey_ref")) return "unknown journey";
  if (flags.includes("legacy_about_field")) return "legacy v4 data";
  if (flags.includes("broken_parent_ref")) return "unknown parent";
  if (flags.includes("inactive_parent_ref")) return "inactive parent";
  if (orphan) return "orphan";
  return "issue";
}

function integrityTooltip(
  kind: "journey" | "narrative" | "role" | "persona",
  flags: string[],
  orphan: boolean,
): string {
  const messages: string[] = [];
  if (flags.includes("missing_role")) {
    messages.push("`role` field is missing — every Persona must belong to a Role.");
  }
  if (flags.includes("broken_role_ref")) {
    messages.push("`role` references a Role that doesn't exist.");
  }
  if (flags.includes("missing_walks")) {
    messages.push("`walks` Role id is missing — required for a Journey.");
  }
  if (flags.includes("broken_walks_ref")) {
    messages.push("`walks` references a Role that doesn't exist.");
  }
  if (flags.includes("missing_about_roles")) {
    messages.push("`about_roles` list is empty — a Narrative requires 1+ Roles.");
  }
  if (flags.includes("broken_about_role_ref")) {
    messages.push("`about_roles` contains a Role that doesn't exist.");
  }
  if (flags.includes("broken_about_persona_ref")) {
    messages.push("`about_personas` contains a Persona that doesn't exist.");
  }
  if (flags.includes("broken_in_journey_ref")) {
    messages.push("`in_journey` references a Journey that doesn't exist.");
  }
  if (flags.includes("legacy_about_field")) {
    messages.push(
      "Legacy v4 `about:` field detected — run `/solera-migrate-v4-to-v5`.",
    );
  }
  if (orphan && !flags.includes("missing_walks")) {
    messages.push("This item's anchor is missing or inactive.");
  }
  if (messages.length === 0) {
    return `${kind} has an integrity issue — open the side panel for details.`;
  }
  return messages.join(" ");
}
