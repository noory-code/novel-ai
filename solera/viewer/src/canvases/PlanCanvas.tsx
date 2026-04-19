import { useMemo } from "react";
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MarkerType,
  type NodeProps,
  Position,
  type Edge,
  type Node,
  type NodeChange,
  applyNodeChanges,
} from "reactflow";
import type { BranchSide, Concept, Graph, Layout, WorkspaceLens } from "../types";
import { ConceptLabel, IdentityConceptHubLabel } from "./PlanLabels";

export const IDENTITY_NODE_ID = "identity";

export interface SelectedNode {
  // v5.0 adds `role` to the Living-axis selection kinds; the Actors canvas
  // emits them, PlanCanvas continues to emit only `identity` and `concept`.
  kind: "identity" | "concept" | "role" | "persona" | "journey" | "narrative";
  id: string;
}

interface PlanCanvasProps {
  graph: Graph;
  lens: WorkspaceLens;
  layout: Layout;
  onLayoutChange: (next: Layout) => void;
  onSelect: (selection: SelectedNode | null) => void;
  selection: SelectedNode | null;
  /** v5.1: workspace path for CRUD. */
  projectPath: string;
  /** v5.1: called after a server mutation so the graph can be re-read. */
  onMutated: () => void;
}

const LEVEL_STEP_X = 280;
const NODE_BAND_HEIGHT = 110;
const BRANCH_GAP = 80;
const DEFAULT_SIDE: BranchSide = "right";

/**
 * Bilateral mindmap layout:
 * - Identity at the origin.
 * - Each top-level Concept carries a `side` hint (from layout metadata); its
 *   subtree then fans outward in that direction (left = x−, right = x+).
 * - A Concept's descendants inherit the branch's side, so positions stay
 *   coherent as the tree grows.
 * - Persisted positions always override auto-layout.
 */
export function PlanCanvas({
  graph,
  lens,
  layout,
  onLayoutChange,
  onSelect,
  selection,
  projectPath,
  onMutated,
}: PlanCanvasProps) {
  const { nodes, edges } = useMemo(
    () => buildFlowElements(graph, lens, layout, selection, projectPath, onMutated),
    [graph, lens, layout, selection],
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

  if (graph.concepts.length === 0) {
    return (
      <div className="flex h-full items-center justify-center px-8 text-center text-slate-500">
        <div className="max-w-md">
          <h2 className="mb-2 text-xl font-semibold text-slate-700">No Concepts yet</h2>
          <p className="text-sm">
            The Plan canvas renders <strong>Concepts</strong> — the living domain map around your
            project's <strong>Identity</strong>, read from <code>.solera/concepts/</code>. Run{" "}
            <code>solera-write-concept</code> to draw one directly, or open the{" "}
            <strong>Service</strong> canvas and click <strong>Propose as Concept</strong> on a
            Narrative.
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
          } else if (node.id.startsWith("concept:")) {
            onSelect({ kind: "concept", id: node.id.slice("concept:".length) });
          }
        }}
        onPaneClick={() => onSelect(null)}
      >
        <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="#e2e8f0" />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}

// -- Identity node: carries both a left and a right source handle so edges
//    can emanate in either direction depending on which side the child sits.

function IdentityNodeView({ data }: NodeProps<{ children: React.ReactNode }>) {
  return (
    <>
      <Handle type="source" position={Position.Left} id="left" style={HANDLE_STYLE} />
      <Handle type="source" position={Position.Right} id="right" style={HANDLE_STYLE} />
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

function buildFlowElements(
  graph: Graph,
  lens: WorkspaceLens,
  layout: Layout,
  selection: SelectedNode | null,
  projectPath: string,
  onMutated: () => void,
): { nodes: Node[]; edges: Edge[] } {
  const byId = new Map(graph.concepts.map((c) => [c.id, c] as const));
  const childrenByParent = new Map<string | null, Concept[]>();
  for (const c of graph.concepts) {
    const key = c.parent && byId.has(c.parent) ? c.parent : null;
    if (!childrenByParent.has(key)) childrenByParent.set(key, []);
    childrenByParent.get(key)!.push(c);
  }

  const topLevels = childrenByParent.get(null) ?? [];
  const autoPositions = new Map<string, { x: number; y: number }>();

  const sideOfTop = (concept: Concept): BranchSide => {
    const stored = layout.nodes[`concept:${concept.id}`]?.side;
    return stored ?? DEFAULT_SIDE;
  };

  // Split top-levels by side; each subtree inherits its root's side.
  const left = topLevels.filter((c) => sideOfTop(c) === "left");
  const right = topLevels.filter((c) => sideOfTop(c) === "right");

  // Build a side map so descendants inherit: {conceptId -> side}
  const sideMap = new Map<string, BranchSide>();
  const propagate = (c: Concept, side: BranchSide) => {
    sideMap.set(c.id, side);
    for (const kid of childrenByParent.get(c.id) ?? []) propagate(kid, side);
  };
  for (const c of left) propagate(c, "left");
  for (const c of right) propagate(c, "right");

  autoPositions.set(IDENTITY_NODE_ID, { x: 0, y: 0 });
  layoutSide(left, "left", childrenByParent, autoPositions);
  layoutSide(right, "right", childrenByParent, autoPositions);

  const nodes: Node[] = [];
  const positionOf = (id: string, fallback: { x: number; y: number }) => {
    const stored = layout.nodes[id];
    if (stored?.x !== undefined && stored?.y !== undefined) {
      return { x: stored.x, y: stored.y };
    }
    return fallback;
  };

  if (graph.identity) {
    const isSelected = selection?.kind === "identity";
    nodes.push({
      id: IDENTITY_NODE_ID,
      type: "identity",
      position: positionOf(IDENTITY_NODE_ID, autoPositions.get(IDENTITY_NODE_ID) ?? { x: 0, y: 0 }),
      data: {
        children: (
          <IdentityConceptHubLabel
            summary={extractFirstSentence(
              graph.identity.mission ?? graph.identity.vision ?? "",
            )}
            projectPath={projectPath}
            onMutated={onMutated}
          />
        ),
      },
      style: {
        background: "#0f172a",
        color: "white",
        border: `${isSelected ? 3 : 2}px solid ${isSelected ? "#fbbf24" : "#0f172a"}`,
        borderRadius: 16,
        padding: "14px 22px",
        minWidth: 200,
        maxWidth: 280,
        cursor: "pointer",
      },
    });
  }

  for (const concept of graph.concepts) {
    const id = `concept:${concept.id}`;
    const isRoot = !concept.parent || !byId.has(concept.parent);
    const isSelected = selection?.kind === "concept" && selection.id === concept.id;
    const fallback = autoPositions.get(concept.id) ?? { x: 0, y: NODE_BAND_HEIGHT };
    const side = sideMap.get(concept.id) ?? DEFAULT_SIDE;
    // Target handle faces Identity / parent (inward); source handle faces
    // children (outward). Inward = opposite of branch direction.
    const targetPos = side === "right" ? Position.Left : Position.Right;
    const sourcePos = side === "right" ? Position.Right : Position.Left;
    nodes.push({
      id,
      position: positionOf(id, fallback),
      data: {
        label: (
          <ConceptLabel
            concept={concept}
            lens={lens}
            isRoot={isRoot}
            projectPath={projectPath}
            onMutated={onMutated}
          />
        ),
      },
      sourcePosition: sourcePos,
      targetPosition: targetPos,
      style: {
        background: conceptBackground(concept, lens),
        border: `${isSelected ? 3 : isRoot ? 2 : 1}px solid ${
          isSelected ? "#6366f1" : conceptBorder(concept, isRoot)
        }`,
        borderRadius: 12,
        padding: isRoot ? "12px 16px" : "8px 12px",
        minWidth: isRoot ? 200 : 170,
        maxWidth: 240,
        cursor: "pointer",
      },
    });
  }

  const edges: Edge[] = [];
  if (graph.identity) {
    for (const top of topLevels) {
      const side = sideMap.get(top.id) ?? DEFAULT_SIDE;
      edges.push({
        id: `identity-${top.id}`,
        source: IDENTITY_NODE_ID,
        sourceHandle: side, // "left" or "right" — matches IdentityNodeView handles
        target: `concept:${top.id}`,
        style: { stroke: "#cbd5e1", strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: "#cbd5e1" },
      });
    }
  }
  for (const concept of graph.concepts) {
    if (!concept.parent || !byId.has(concept.parent)) continue;
    edges.push({
      id: `parent-${concept.id}`,
      source: `concept:${concept.parent}`,
      target: `concept:${concept.id}`,
      style: { stroke: "#cbd5e1", strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#cbd5e1" },
    });
  }
  for (const e of graph.concept_edges) {
    edges.push({
      id: e.id,
      source: `concept:${e.from}`,
      target: `concept:${e.to}`,
      label: e.label || undefined,
      labelStyle: { fontSize: 11, fill: "#475569" },
      style: { stroke: "#94a3b8", strokeDasharray: "4 3" },
    });
  }

  return { nodes, edges };
}

function layoutSide(
  roots: Concept[],
  side: BranchSide,
  childrenByParent: Map<string | null, Concept[]>,
  positions: Map<string, { x: number; y: number }>,
): void {
  if (roots.length === 0) return;
  const dir = side === "right" ? 1 : -1;
  const rootX = dir * LEVEL_STEP_X;

  // Precompute each root's subtree height; stack them vertically centered
  // at y=0 so Identity sits at the visual midpoint.
  const heights = roots.map((r) => subtreeHeight(r, childrenByParent));
  const totalHeight =
    heights.reduce((acc, h) => acc + h, 0) + BRANCH_GAP * Math.max(roots.length - 1, 0);
  let cursorY = -totalHeight / 2;
  for (let i = 0; i < roots.length; i++) {
    const centerY = cursorY + heights[i] / 2;
    placeSubtree(roots[i], childrenByParent, positions, rootX, centerY, dir);
    cursorY += heights[i] + BRANCH_GAP;
  }
}

function placeSubtree(
  concept: Concept,
  childrenByParent: Map<string | null, Concept[]>,
  positions: Map<string, { x: number; y: number }>,
  x: number,
  centerY: number,
  dir: 1 | -1,
): void {
  positions.set(concept.id, { x, y: centerY });
  const kids = childrenByParent.get(concept.id) ?? [];
  if (kids.length === 0) return;
  const childX = x + dir * LEVEL_STEP_X;
  const childHeights = kids.map((k) => subtreeHeight(k, childrenByParent));
  const total = childHeights.reduce((a, b) => a + b, 0);
  let cursorY = centerY - total / 2;
  for (let i = 0; i < kids.length; i++) {
    const my = cursorY + childHeights[i] / 2;
    placeSubtree(kids[i], childrenByParent, positions, childX, my, dir);
    cursorY += childHeights[i];
  }
}

function subtreeHeight(
  concept: Concept,
  childrenByParent: Map<string | null, Concept[]>,
): number {
  const kids = childrenByParent.get(concept.id) ?? [];
  if (kids.length === 0) return NODE_BAND_HEIGHT;
  return kids.reduce((acc, k) => acc + subtreeHeight(k, childrenByParent), 0);
}

function extractFirstSentence(text: string): string {
  for (const raw of text.split("\n")) {
    const trimmed = raw.trim();
    if (!trimmed) continue;
    if (trimmed.startsWith("#")) continue;
    if (trimmed.startsWith("<!--")) continue;
    return trimmed.replace(/^>\s*/, "").replace(/\*\*/g, "").replace(/<!--.*?-->/g, "").trim();
  }
  return "";
}

function conceptBackground(c: Concept, lens: WorkspaceLens): string {
  if (c.status === "archived") return "#f1f5f9";
  if (c.status === "deprecated") return "#fef2f2";
  if (lens === "live" && c.current_shape.includes("no Stories")) return "#fffbeb";
  return "#ffffff";
}

function conceptBorder(c: Concept, isRoot: boolean): string {
  if (c.status === "archived") return "#cbd5e1";
  if (c.status === "deprecated") return "#fecaca";
  return isRoot ? "#6366f1" : "#c7d2fe";
}
