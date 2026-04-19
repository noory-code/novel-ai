import { useMemo } from "react";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  Position,
  type Edge,
  type Node,
  type NodeChange,
  applyNodeChanges,
} from "reactflow";
import type { Graph, Layout, Persona, Journey, Narrative } from "../types";
import type { SelectedNode } from "./PlanCanvas";

interface ServiceCanvasProps {
  graph: Graph;
  layout: Layout;
  onLayoutChange: (next: Layout) => void;
  onSelect: (selection: SelectedNode | null) => void;
  selection: SelectedNode | null;
}

// Three-column swimlane: Personas on the left, Journeys for each Persona in the
// middle, Narratives anchored to their Journey/Persona on the right. Loose
// Narratives (no `in_journey`) cluster in a tray at the bottom.
//
// Coordinates use a fixed band per Persona; Journeys stack vertically within
// the band, and Narratives stack vertically next to their anchor. Persisted
// positions in `layout.nodes` always override auto-layout.

const COL_PERSONA_X = 0;
const COL_JOURNEY_X = 360;
const COL_NARRATIVE_X = 760;

const PERSONA_BAND_GAP = 60; // extra space between Persona bands
const JOURNEY_ROW_GAP = 28;
const NARRATIVE_ROW_GAP = 24;

const PERSONA_NODE_HEIGHT = 140;
const JOURNEY_NODE_HEIGHT = 110;
const NARRATIVE_NODE_HEIGHT = 110;

const LOOSE_NARRATIVE_BAND_GAP = 80;

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
  const journeysByPersona = new Map<string, Journey[]>();
  for (const j of graph.journeys) {
    const key = j.walks || "__orphan__";
    if (!journeysByPersona.has(key)) journeysByPersona.set(key, []);
    journeysByPersona.get(key)!.push(j);
  }

  const narrativesByJourney = new Map<string, Narrative[]>();
  const looseNarratives: Narrative[] = [];
  for (const n of graph.narratives) {
    if (n.in_journey) {
      if (!narrativesByJourney.has(n.in_journey)) narrativesByJourney.set(n.in_journey, []);
      narrativesByJourney.get(n.in_journey)!.push(n);
    } else {
      looseNarratives.push(n);
    }
  }

  // Auto-layout: walk personas top-to-bottom, allocating each one a band whose
  // height accommodates its journeys + their attached narratives.
  const autoPositions = new Map<string, { x: number; y: number }>();
  let cursorY = 0;
  let maxBandBottom = 0;

  const allocatePersonaBand = (persona: Persona) => {
    const ownJourneys = journeysByPersona.get(persona.id) ?? [];
    const journeyCount = Math.max(ownJourneys.length, 1);
    const journeysHeight = journeyCount * (JOURNEY_NODE_HEIGHT + JOURNEY_ROW_GAP) - JOURNEY_ROW_GAP;
    const narrativesForBand = ownJourneys.flatMap(
      (j) => narrativesByJourney.get(j.id) ?? [],
    );
    const narrativesHeight =
      Math.max(narrativesForBand.length, 0) * (NARRATIVE_NODE_HEIGHT + NARRATIVE_ROW_GAP) -
      NARRATIVE_ROW_GAP;
    const bandHeight = Math.max(PERSONA_NODE_HEIGHT, journeysHeight, narrativesHeight);

    autoPositions.set(`persona:${persona.id}`, {
      x: COL_PERSONA_X,
      y: cursorY,
    });

    let journeyY = cursorY;
    let narrativeCursorY = cursorY;
    for (const j of ownJourneys) {
      autoPositions.set(`journey:${j.id}`, { x: COL_JOURNEY_X, y: journeyY });
      journeyY += JOURNEY_NODE_HEIGHT + JOURNEY_ROW_GAP;
      for (const n of narrativesByJourney.get(j.id) ?? []) {
        autoPositions.set(`narrative:${n.id}`, {
          x: COL_NARRATIVE_X,
          y: narrativeCursorY,
        });
        narrativeCursorY += NARRATIVE_NODE_HEIGHT + NARRATIVE_ROW_GAP;
      }
    }

    maxBandBottom = Math.max(maxBandBottom, cursorY + bandHeight);
    cursorY += bandHeight + PERSONA_BAND_GAP;
  };

  for (const persona of personas) {
    allocatePersonaBand(persona);
  }

  // Orphan Journeys (walks a Persona that doesn't exist) get an "Orphan" band.
  const orphanJourneys = journeysByPersona.get("__orphan__") ?? [];
  const journeysWithOrphanWalks = graph.journeys.filter(
    (j) => j.walks && !personas.some((p) => p.id === j.walks),
  );
  const allOrphans = [...orphanJourneys, ...journeysWithOrphanWalks];
  let orphanY = cursorY;
  for (const j of allOrphans) {
    autoPositions.set(`journey:${j.id}`, { x: COL_JOURNEY_X, y: orphanY });
    for (const n of narrativesByJourney.get(j.id) ?? []) {
      autoPositions.set(`narrative:${n.id}`, { x: COL_NARRATIVE_X, y: orphanY });
      orphanY += NARRATIVE_NODE_HEIGHT + NARRATIVE_ROW_GAP;
    }
    orphanY += JOURNEY_NODE_HEIGHT + JOURNEY_ROW_GAP;
  }
  maxBandBottom = Math.max(maxBandBottom, orphanY);

  // Loose Narratives tray below everything.
  let looseY = maxBandBottom + LOOSE_NARRATIVE_BAND_GAP;
  for (const n of looseNarratives) {
    autoPositions.set(`narrative:${n.id}`, { x: COL_NARRATIVE_X, y: looseY });
    looseY += NARRATIVE_NODE_HEIGHT + NARRATIVE_ROW_GAP;
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
      position: positionOf(id, autoPositions.get(id) ?? { x: COL_PERSONA_X, y: 0 }),
      data: { label: renderPersonaLabel(persona) },
      sourcePosition: Position.Right,
      style: {
        background: persona.status === "deprecated" ? "#fef3c7" : "#fdf2f8",
        border: `${isSelected ? 3 : 2}px solid ${isSelected ? "#6366f1" : "#f9a8d4"}`,
        borderRadius: 14,
        padding: "12px 16px",
        minWidth: 280,
        maxWidth: 320,
        cursor: "pointer",
      },
    });
  }

  for (const journey of graph.journeys) {
    const id = `journey:${journey.id}`;
    const isSelected = selection?.kind === "journey" && selection.id === journey.id;
    const orphan =
      !journey.walks || !personas.some((p) => p.id === journey.walks);
    nodes.push({
      id,
      position: positionOf(id, autoPositions.get(id) ?? { x: COL_JOURNEY_X, y: 0 }),
      data: { label: renderJourneyLabel(journey, orphan) },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      style: {
        background: journey.status === "deprecated" ? "#fef3c7" : "#eff6ff",
        border: `${isSelected ? 3 : 2}px solid ${
          isSelected ? "#6366f1" : orphan ? "#fb923c" : "#93c5fd"
        }`,
        borderRadius: 12,
        padding: "10px 14px",
        minWidth: 320,
        maxWidth: 380,
        cursor: "pointer",
      },
    });
  }

  for (const narrative of graph.narratives) {
    const id = `narrative:${narrative.id}`;
    const isSelected =
      selection?.kind === "narrative" && selection.id === narrative.id;
    nodes.push({
      id,
      position: positionOf(id, autoPositions.get(id) ?? { x: COL_NARRATIVE_X, y: 0 }),
      data: { label: renderNarrativeLabel(narrative) },
      targetPosition: Position.Left,
      style: {
        background: narrative.status === "deprecated" ? "#fef3c7" : "#f0fdf4",
        border: `${isSelected ? 3 : 2}px solid ${
          isSelected
            ? "#6366f1"
            : narrative.proposes.length > 0
              ? "#86efac"
              : "#bbf7d0"
        }`,
        borderRadius: 12,
        padding: "10px 14px",
        minWidth: 280,
        maxWidth: 340,
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
  return (
    <div className="flex flex-col gap-1 text-left">
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wide text-blue-500">Journey</span>
        {orphan && (
          <span className="text-[10px] uppercase tracking-wide text-orange-600">
            ⚠ orphan
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
  return (
    <div className="flex flex-col gap-1 text-left">
      <div className="flex items-center gap-2">
        <span className={`text-[10px] uppercase tracking-wide ${formColor}`}>
          {narrative.form.replace("_", " ")}
        </span>
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
