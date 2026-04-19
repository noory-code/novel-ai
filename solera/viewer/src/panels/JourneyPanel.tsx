import type { Graph } from "../types";
import {
  EmptyState,
  IntegrityBanner,
  MetaRow,
  Section,
  SectionTitle,
  StatusChip,
  resolveName,
} from "./helpers";

export function JourneyBody({ graph, journeyId }: { graph: Graph; journeyId: string }) {
  const journey = graph.journeys.find((j) => j.id === journeyId);
  if (!journey) return <EmptyState text="Journey not found." />;

  const persona = graph.personas.find((p) => p.id === journey.walks);
  const narratives = graph.narratives.filter((n) => n.in_journey === journey.id);
  const orphanWalksRef = Boolean(journey.walks) && !persona;

  return (
    <div className="space-y-4">
      <header>
        <h2 className="text-lg font-semibold text-ink">{journey.name}</h2>
        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-slate-400">
          <span className="font-mono">{journey.id}</span>
          <StatusChip status={journey.status} />
          {(journey.integrity.length > 0 || orphanWalksRef) && (
            <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-semibold text-red-700 ring-1 ring-red-300">
              ⚠ integrity
            </span>
          )}
        </div>
      </header>
      {journey.integrity.includes("missing_walks") && (
        <IntegrityBanner
          title="This Journey has no Persona."
          detail={
            <>
              A Journey must declare the Persona it is walked by via{" "}
              <code>walks:</code> in the frontmatter.
            </>
          }
          repair={`/solera-write-journey mode=update journey_id=${journey.id}`}
        />
      )}
      {orphanWalksRef && !journey.integrity.includes("missing_walks") && (
        <IntegrityBanner
          title={`walks Persona "${journey.walks}" is missing or inactive.`}
          detail="Draw the Persona first, or update this Journey's `walks` to a known active Persona."
          repair={`/solera-write-persona mode=create persona_id=${journey.walks}`}
        />
      )}
      <MetaRow
        label="Walks"
        value={persona ? persona.name : journey.walks || "(none — orphan)"}
      />
      {journey.parent && (
        <MetaRow label="Parent" value={resolveName(graph.journeys, journey.parent)} />
      )}
      <Section title="Trigger" body={journey.trigger} tone="north-star" />
      {journey.steps.length > 0 ? (
        <div>
          <SectionTitle title="Steps" tone="sketch" />
          <ol className="space-y-2 text-[12px] text-slate-700">
            {journey.steps.map((s) => (
              <li key={s.n} className="rounded border border-slate-200 p-2">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-wide text-slate-400">
                  <span className="font-mono">#{String(s.n).padStart(2, "0")}</span>
                  <span>{s.stage}</span>
                  <span>·</span>
                  <span>{s.touchpoint}</span>
                  {s.emotion && <span className="ml-auto text-base">{s.emotion}</span>}
                </div>
                <div className="mt-1 text-slate-700">{s.step}</div>
                {s.pain && s.pain !== "—" && (
                  <div className="mt-1 text-[11px] text-rose-600">pain: {s.pain}</div>
                )}
              </li>
            ))}
          </ol>
        </div>
      ) : (
        <div>
          <SectionTitle title="Steps" tone="sketch" />
          <p className="text-[12px] italic text-slate-400">no steps yet</p>
        </div>
      )}
      <Section title="Outcome" body={journey.outcome} tone="live" />
      {narratives.length > 0 && (
        <MetaRow
          label="Narratives"
          value={`${narratives.length} anchored`}
        />
      )}
    </div>
  );
}
