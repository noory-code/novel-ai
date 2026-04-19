import type { Graph } from "../types";
import {
  BulletSection,
  EmptyState,
  MetaRow,
  Section,
  StatusChip,
  resolveName,
} from "./helpers";

export function PersonaBody({ graph, personaId }: { graph: Graph; personaId: string }) {
  const persona = graph.personas.find((p) => p.id === personaId);
  if (!persona) return <EmptyState text="Persona not found." />;

  const journeys = graph.journeys.filter((j) => j.walks === persona.id);
  const narratives = graph.narratives.filter((n) => n.about.includes(persona.id));
  const children = graph.personas.filter((p) => p.parent === persona.id);

  return (
    <div className="space-y-4">
      <header>
        <h2 className="text-lg font-semibold text-ink">{persona.name}</h2>
        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-slate-400">
          <span className="font-mono">{persona.id}</span>
          <StatusChip status={persona.status} />
        </div>
      </header>
      {persona.parent && (
        <MetaRow label="Parent" value={resolveName(graph.personas, persona.parent)} />
      )}
      {children.length > 0 && (
        <MetaRow label="Children" value={children.map((c) => c.name).join(", ")} />
      )}
      <Section title="Identity" body={persona.identity} tone="north-star" />
      <BulletSection title="Goals" items={persona.goals} />
      <BulletSection title="Pains" items={persona.pains} />
      <BulletSection title="Triggers" items={persona.triggers} />
      <BulletSection title="Quotes" items={persona.quotes} />
      {persona.channels && <Section title="Channels" body={persona.channels} />}
      {journeys.length > 0 && (
        <MetaRow
          label="Journeys"
          value={journeys.map((j) => j.name).join(", ")}
        />
      )}
      {narratives.length > 0 && (
        <MetaRow
          label="Narratives"
          value={`${narratives.length} narrative${narratives.length === 1 ? "" : "s"}`}
        />
      )}
    </div>
  );
}
