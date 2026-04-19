import type { Graph } from "../types";
import {
  BulletSection,
  EmptyState,
  IntegrityBanner,
  MetaRow,
  Section,
  StatusChip,
  resolveName,
} from "./helpers";

export function PersonaBody({ graph, personaId }: { graph: Graph; personaId: string }) {
  const persona = graph.personas.find((p) => p.id === personaId);
  if (!persona) return <EmptyState text="Persona not found." />;

  // v5.0: Journeys now walk Roles; Persona sees the Journeys that explicitly
  // include it on `walked_by`. Narratives: explicit `about_personas` entry.
  const role = graph.roles.find((r) => r.id === persona.role);
  const journeys = graph.journeys.filter((j) => j.walked_by.includes(persona.id));
  const narratives = graph.narratives.filter((n) =>
    n.about_personas.includes(persona.id),
  );
  const children = graph.personas.filter((p) => p.parent === persona.id);

  return (
    <div className="space-y-4">
      <header>
        <h2 className="text-lg font-semibold text-ink">{persona.name}</h2>
        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-slate-400">
          <span className="font-mono">{persona.id}</span>
          <StatusChip status={persona.status} />
          {persona.integrity.length > 0 && (
            <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-semibold text-red-700 ring-1 ring-red-300">
              ⚠ integrity
            </span>
          )}
        </div>
      </header>
      {persona.integrity.includes("missing_role") && (
        <IntegrityBanner
          title="This Persona has no Role."
          detail={
            <>
              Every Persona must declare a Role via <code>role:</code> in the
              frontmatter. Without it the archetype is disconnected on the
              Actors canvas.
            </>
          }
          repair={`/solera-write-persona mode=update persona_id=${persona.id}`}
        />
      )}
      {persona.integrity.includes("broken_role_ref") && (
        <IntegrityBanner
          title={`role "${persona.role}" does not exist.`}
          detail="Draw the Role first, or update this Persona's role to a known active Role."
          repair={`/solera-write-role mode=create role_id=${persona.role}`}
        />
      )}
      <MetaRow
        label="Role"
        value={role ? role.name : persona.role || "(none)"}
      />
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
