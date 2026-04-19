import type { SelectedNode } from "./canvases/PlanCanvas";
import { ConceptBody } from "./panels/ConceptPanel";
import { EmptyState } from "./panels/helpers";
import { IdentityBody } from "./panels/IdentityPanel";
import { JourneyBody } from "./panels/JourneyPanel";
import { NarrativeBody } from "./panels/NarrativePanel";
import { PersonaBody } from "./panels/PersonaPanel";
import { RoleBody } from "./panels/RolePanel";
import type { Graph, Layout } from "./types";

// ---------------------------------------------------------------------------
// Side panel container.
//
// The concrete body for each selection kind lives under `./panels/`:
//
//   IdentityPanel     → Identity → mission / vision / values / tone / goals
//   ConceptPanel      → Concept  → intent / design / shape / parent / side
//   PersonaPanel      → Persona  → identity / goals / pains / triggers / quotes
//   JourneyPanel      → Journey  → trigger / steps / outcome (+ integrity)
//   NarrativePanel    → Narrative → statement / context / cues / proposes
//                                   + "Propose as Concept" action
//
// Shared atoms (Section / MetaRow / StatusChip / IntegrityBanner / …) live in
// `./panels/helpers.tsx`. This file owns only the outer aside + kind-routing.
// ---------------------------------------------------------------------------

interface SidePanelProps {
  graph: Graph;
  selection: SelectedNode | null;
  projectPath: string;
  layout: Layout;
  onClose: () => void;
  onMutated: () => void;
  onLayoutChange: (next: Layout) => void;
}

export function SidePanel({
  graph,
  selection,
  projectPath,
  layout,
  onClose,
  onMutated,
  onLayoutChange,
}: SidePanelProps) {
  if (selection === null) return null;
  const headerLabel: Record<SelectedNode["kind"], string> = {
    identity: "Identity",
    concept: "Concept",
    role: "Role",
    persona: "Persona",
    journey: "Journey",
    narrative: "Narrative",
  };
  return (
    <aside className="flex w-96 flex-col border-l border-slate-200 bg-white">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2">
        <span className="text-[11px] font-semibold uppercase tracking-widest text-slate-400">
          {headerLabel[selection.kind]}
        </span>
        <button
          onClick={onClose}
          className="rounded px-2 py-0.5 text-sm text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          aria-label="Close panel"
        >
          ✕
        </button>
      </div>
      <div className="flex-1 overflow-auto px-4 py-3 text-sm">
        {renderSelectionBody({
          selection,
          graph,
          projectPath,
          layout,
          onMutated,
          onLayoutChange,
        })}
      </div>
    </aside>
  );
}

function renderSelectionBody({
  selection,
  graph,
  projectPath,
  layout,
  onMutated,
  onLayoutChange,
}: {
  selection: SelectedNode;
  graph: Graph;
  projectPath: string;
  layout: Layout;
  onMutated: () => void;
  onLayoutChange: (next: Layout) => void;
}): React.ReactNode {
  switch (selection.kind) {
    case "identity":
      return graph.identity !== null ? (
        <IdentityBody identity={graph.identity} />
      ) : (
        <EmptyState text="Identity not found." />
      );
    case "concept":
      return (
        <ConceptBody
          graph={graph}
          conceptId={selection.id}
          projectPath={projectPath}
          layout={layout}
          onMutated={onMutated}
          onLayoutChange={onLayoutChange}
        />
      );
    case "role":
      return <RoleBody graph={graph} roleId={selection.id} />;
    case "persona":
      return <PersonaBody graph={graph} personaId={selection.id} />;
    case "journey":
      return <JourneyBody graph={graph} journeyId={selection.id} />;
    case "narrative":
      return (
        <NarrativeBody
          graph={graph}
          narrativeId={selection.id}
          projectPath={projectPath}
          onMutated={onMutated}
        />
      );
  }
}
