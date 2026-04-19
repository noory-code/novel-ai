import { useMemo } from "react";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  type Edge,
  type Node,
  type NodeChange,
  applyNodeChanges,
} from "reactflow";
import type { Graph, Journey, Layout, Narrative, Persona } from "../types";
import type { SelectedNode } from "./PlanCanvas";

interface ServiceCanvasProps {
  graph: Graph;
  layout: Layout;
  onLayoutChange: (next: Layout) => void;
  onSelect: (selection: SelectedNode | null) => void;
  selection: SelectedNode | null;
}

// Persona-centric radial mindmap:
//   - Each Persona is the hub of its own cluster.
//   - Its Journeys sit on the inner ring (distributed evenly around the
//     hub, clockwise from 12 o'clock).
//   - Narratives sit on the outer ring:
//       - If the Narrative has `in_journey`, it sits at approximately the
//         same angle as that Journey (slightly fanned out if multiple).
//       - Loose Narratives (about the Persona but no in_journey) fill the
//         angular gaps between Journeys. If there are no Journeys, they
//         spread evenly around the hub.
//   - Multiple Personas → multiple clusters, arranged on a wide grid
//     (CLUSTERS_PER_ROW per row). User drag positions are persisted via
//     `layout.nodes` and override auto-layout on subsequent renders.
//   - Orphan Journeys (walks unknown) and fully-loose Narratives (no
//     resolvable `about` Persona) get a horizontal orphan row below the
//     persona clusters so the integrity banners the SidePanel surfaces are
//     easy to find.
//
// This honours the "UI must be mindmap graph" principle (feedback memory
// `feedback_topview_purpose.md`) — radial is the shape human cognition uses
// for "who pressures what".

const CLUSTER_SPACING_X = 900;
const CLUSTER_SPACING_Y = 900;
const CLUSTERS_PER_ROW = 3;

const JOURNEY_RING_RADIUS = 220;
const NARRATIVE_RING_RADIUS = 400;
const NARRATIVE_EXTRA_LAYER_STEP = 110; // extra radius per overflow layer

const ORPHAN_ROW_GAP = 260;
const ORPHAN_STEP_X = 360;

export function ServiceCanvas({
  graph,
  layout,
  onLayoutChange,
  onSelect,
  selection,
}: ServiceCanvasProps) {
  const { nodes, edges } = useMemo(
    () => buildServiceFlowElements(graph, layout, selection),
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

  if (graph.personas.length === 0 && graph.journeys.length === 0 && graph.narratives.length === 0) {
    return (
      <div className="flex h-full items-center justify-center px-8 text-center text-slate-500">
        <div className="max-w-md">
          <h2 className="mb-2 text-xl font-semibold text-slate-700">No service drawings yet</h2>
          <p className="text-sm">
            The Service canvas renders <strong>Personas</strong>, <strong>Journeys</strong>, and{" "}
            <strong>Narratives</strong> from <code>.solera/personas/</code>,{" "}
            <code>.solera/journeys/</code>, and <code>.solera/narratives/</code>. Run{" "}
            <code>solera-write-persona</code> to draw your first one.
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
        fitView
        fitViewOptions={{ padding: 0.2 }}
        nodesDraggable
        nodesConnectable={false}
        elementsSelectable
        onNodesChange={handleNodesChange}
        onNodeClick={(_evt, node) => {
          if (node.id.startsWith("persona:")) {
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

export function buildServiceFlowElements(
  graph: Graph,
  layout: Layout,
  selection: SelectedNode | null,
): { nodes: Node[]; edges: Edge[] } {
  const personas = graph.personas;
  const personaIdSet = new Set(personas.map((p) => p.id));

  // Auto-layout positions keyed by `kind:id`.
  const autoPositions = new Map<string, { x: number; y: number }>();

  // Each Persona owns a radial cluster centred on a grid slot.
  personas.forEach((persona, i) => {
    const row = Math.floor(i / CLUSTERS_PER_ROW);
    const col = i % CLUSTERS_PER_ROW;
    const cx = col * CLUSTER_SPACING_X;
    const cy = row * CLUSTER_SPACING_Y;
    const ownJourneys = graph.journeys.filter((j) => j.walks === persona.id);
    const ownNarratives = graph.narratives.filter((n) =>
      n.about.some((aboutId) => aboutId === persona.id),
    );
    layoutPersonaCluster(cx, cy, persona, ownJourneys, ownNarratives, autoPositions);
  });

  // Orphans: Journeys pointing at a Persona that doesn't exist (or with empty
  // `walks`), plus Narratives whose entire `about` list is unresolvable. Put
  // them on a horizontal row below the Persona clusters so the integrity
  // banners in the SidePanel are easy to find.
  const orphanJourneys = graph.journeys.filter(
    (j) => !j.walks || !personaIdSet.has(j.walks),
  );
  const orphanNarratives = graph.narratives.filter(
    (n) => n.about.length === 0 || !n.about.some((a) => personaIdSet.has(a)),
  );
  if (orphanJourneys.length > 0 || orphanNarratives.length > 0) {
    const orphanRow = Math.ceil(personas.length / CLUSTERS_PER_ROW);
    const baseY = orphanRow * CLUSTER_SPACING_Y;
    orphanJourneys.forEach((j, i) => {
      autoPositions.set(`journey:${j.id}`, { x: i * ORPHAN_STEP_X, y: baseY });
    });
    orphanNarratives.forEach((n, i) => {
      autoPositions.set(`narrative:${n.id}`, {
        x: i * ORPHAN_STEP_X,
        y: baseY + ORPHAN_ROW_GAP,
      });
    });
  }

  const positionOf = (id: string, fallback: { x: number; y: number }) => {
    const stored = layout.nodes[id];
    if (stored?.x !== undefined && stored?.y !== undefined) {
      return { x: stored.x, y: stored.y };
    }
    return fallback;
  };

  const nodes: Node[] = [];

  for (const persona of personas) {
    const id = `persona:${persona.id}`;
    const isSelected = selection?.kind === "persona" && selection.id === persona.id;
    nodes.push({
      id,
      position: positionOf(id, autoPositions.get(id) ?? { x: 0, y: 0 }),
      data: { label: renderPersonaLabel(persona) },
      style: {
        background: persona.status === "deprecated" ? "#fef3c7" : "#fdf2f8",
        border: `${isSelected ? 3 : 2}px solid ${isSelected ? "#6366f1" : "#f9a8d4"}`,
        borderRadius: 14,
        padding: "12px 16px",
        minWidth: 260,
        maxWidth: 300,
        cursor: "pointer",
      },
    });
  }

  for (const journey of graph.journeys) {
    const id = `journey:${journey.id}`;
    const isSelected = selection?.kind === "journey" && selection.id === journey.id;
    const orphan =
      !journey.walks || !personas.some((p) => p.id === journey.walks);
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
        minWidth: 280,
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

  // ---- Edges ----------------------------------------------------------------

  const edges: Edge[] = [];

  // Persona ←→ Journey (walks)
  for (const journey of graph.journeys) {
    if (!journey.walks) continue;
    if (!personas.some((p) => p.id === journey.walks)) continue;
    edges.push({
      id: `walks-${journey.id}`,
      source: `persona:${journey.walks}`,
      target: `journey:${journey.id}`,
      label: "walks",
      labelStyle: { fontSize: 10, fill: "#7c3aed" },
      style: { stroke: "#c4b5fd", strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#c4b5fd" },
    });
  }

  // Narrative ←→ Persona (about) and Narrative ←→ Journey (in_journey)
  const personaIds = new Set(personas.map((p) => p.id));
  const journeyIds = new Set(graph.journeys.map((j) => j.id));
  for (const narrative of graph.narratives) {
    if (narrative.in_journey && journeyIds.has(narrative.in_journey)) {
      edges.push({
        id: `in-journey-${narrative.id}`,
        source: `journey:${narrative.in_journey}`,
        target: `narrative:${narrative.id}`,
        style: { stroke: "#94a3b8", strokeDasharray: "4 3" },
      });
    } else {
      // No journey anchor — connect to first known Persona via dashed line so
      // the narrative is visually rooted somewhere.
      const anchor = narrative.about.find((p) => personaIds.has(p));
      if (anchor) {
        edges.push({
          id: `about-${narrative.id}-${anchor}`,
          source: `persona:${anchor}`,
          target: `narrative:${narrative.id}`,
          style: { stroke: "#cbd5e1", strokeDasharray: "2 4" },
        });
      }
    }
  }

  return { nodes, edges };
}

// ---- Node label renderers ---------------------------------------------------

function layoutPersonaCluster(
  cx: number,
  cy: number,
  persona: Persona,
  journeys: Journey[],
  narratives: Narrative[],
  positions: Map<string, { x: number; y: number }>,
): void {
  // Persona is the hub.
  positions.set(`persona:${persona.id}`, { x: cx, y: cy });

  const nJ = journeys.length;
  const journeyAngles = new Map<string, number>();

  // Inner ring: distribute journeys starting from 12 o'clock, clockwise.
  // With only one Journey this still anchors it at the top; with many, each
  // gets ``2π/N`` of angular space.
  journeys.forEach((j, i) => {
    const angle = -Math.PI / 2 + (i / Math.max(nJ, 1)) * 2 * Math.PI;
    journeyAngles.set(j.id, angle);
    positions.set(`journey:${j.id}`, {
      x: cx + JOURNEY_RING_RADIUS * Math.cos(angle),
      y: cy + JOURNEY_RING_RADIUS * Math.sin(angle),
    });
  });

  // Split narratives: anchored to a Journey (in_journey) vs loose (only
  // `about` this Persona). Anchored narratives ride the outer ring near
  // their journey's angle; loose ones fill the gaps between journeys.
  const inJourneyNars = new Map<string, Narrative[]>();
  const looseNars: Narrative[] = [];
  for (const n of narratives) {
    if (n.in_journey && journeyAngles.has(n.in_journey)) {
      const bucket = inJourneyNars.get(n.in_journey) ?? [];
      bucket.push(n);
      inJourneyNars.set(n.in_journey, bucket);
    } else {
      looseNars.push(n);
    }
  }

  // Anchored narratives: fan them out around their journey's angle. With a
  // single anchored narrative the fan collapses to zero offset; with many,
  // cap the spread so neighbouring journeys' narratives don't overlap.
  for (const [journeyId, nars] of inJourneyNars.entries()) {
    const baseAngle = journeyAngles.get(journeyId)!;
    const maxSpread = Math.min(0.35, Math.PI / Math.max(nJ * 2, 2));
    nars.forEach((n, i) => {
      const offset =
        nars.length === 1 ? 0 : -maxSpread + (i / (nars.length - 1)) * (maxSpread * 2);
      const angle = baseAngle + offset;
      positions.set(`narrative:${n.id}`, {
        x: cx + NARRATIVE_RING_RADIUS * Math.cos(angle),
        y: cy + NARRATIVE_RING_RADIUS * Math.sin(angle),
      });
    });
  }

  // Loose narratives: if no Journeys exist, spread evenly around the hub.
  // Otherwise place them at the midpoints of the journey arcs, wrapping out
  // to an additional radial layer once we run out of unique midpoints.
  if (looseNars.length > 0) {
    if (nJ === 0) {
      looseNars.forEach((n, i) => {
        const angle =
          -Math.PI / 2 + (i / looseNars.length) * 2 * Math.PI;
        positions.set(`narrative:${n.id}`, {
          x: cx + NARRATIVE_RING_RADIUS * Math.cos(angle),
          y: cy + NARRATIVE_RING_RADIUS * Math.sin(angle),
        });
      });
    } else {
      looseNars.forEach((n, i) => {
        const slot = i % nJ;
        const layer = Math.floor(i / nJ);
        const midpointAngle =
          -Math.PI / 2 + ((slot + 0.5) / nJ) * 2 * Math.PI;
        const radius = NARRATIVE_RING_RADIUS + layer * NARRATIVE_EXTRA_LAYER_STEP;
        positions.set(`narrative:${n.id}`, {
          x: cx + radius * Math.cos(midpointAngle),
          y: cy + radius * Math.sin(midpointAngle),
        });
      });
    }
  }
}

function renderPersonaLabel(persona: Persona): React.ReactNode {
  const firstSentence = persona.identity.split(/[.!?]\s/)[0]?.trim() ?? "";
  return (
    <div className="flex flex-col gap-1 text-left">
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wide text-pink-500">Persona</span>
        {persona.status !== "active" && (
          <span className="text-[10px] uppercase tracking-wide text-amber-600">
            {persona.status}
          </span>
        )}
      </div>
      <div className="text-base font-semibold text-slate-800">{persona.name}</div>
      {firstSentence && (
        <div className="line-clamp-3 text-xs text-slate-600">{firstSentence}</div>
      )}
      {persona.goals.length > 0 && (
        <div className="mt-1 text-[11px] text-slate-500">
          Goals: <span className="text-slate-700">{persona.goals[0]}</span>
          {persona.goals.length > 1 && (
            <span className="text-slate-400"> · +{persona.goals.length - 1}</span>
          )}
        </div>
      )}
    </div>
  );
}

function renderJourneyLabel(journey: Journey, orphan: boolean): React.ReactNode {
  const hasIntegrityIssue = journey.integrity.length > 0 || orphan;
  return (
    <div className="flex flex-col gap-1 text-left">
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wide text-blue-500">Journey</span>
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
          <span className="text-[10px] uppercase tracking-wide text-amber-600">
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
      ? "text-violet-500"
      : narrative.form === "scenario"
        ? "text-teal-500"
        : "text-emerald-500";
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
          <span className="text-[10px] uppercase tracking-wide text-amber-600">
            {narrative.status}
          </span>
        )}
      </div>
      <div className="text-xs italic leading-snug text-slate-700 line-clamp-3">
        {narrative.statement || <span className="text-slate-400">(no statement)</span>}
      </div>
      {narrative.proposes.length > 0 && (
        <div className="mt-1 text-[11px] text-emerald-600">
          → proposes {narrative.proposes.length} Concept
          {narrative.proposes.length === 1 ? "" : "s"}
        </div>
      )}
    </div>
  );
}

function integrityShortLabel(flags: string[], orphan: boolean): string {
  if (flags.includes("missing_walks")) return "no walks";
  if (flags.includes("missing_about")) return "no about";
  if (flags.includes("broken_in_journey_ref")) return "unknown journey";
  if (orphan) return "orphan";
  return "issue";
}

function integrityTooltip(
  kind: "journey" | "narrative",
  flags: string[],
  orphan: boolean,
): string {
  const messages: string[] = [];
  if (flags.includes("missing_walks")) {
    messages.push("`walks` Persona id is missing — required for a Journey.");
  }
  if (flags.includes("missing_about")) {
    messages.push("`about` list is empty — a Narrative requires 1+ Personas.");
  }
  if (flags.includes("broken_in_journey_ref")) {
    messages.push("`in_journey` references a Journey that doesn't exist.");
  }
  if (orphan && !flags.includes("missing_walks")) {
    messages.push("This Journey walks a Persona that doesn't exist or is inactive.");
  }
  if (messages.length === 0) {
    return `${kind} has an integrity issue — open the side panel for details.`;
  }
  return messages.join(" ");
}
