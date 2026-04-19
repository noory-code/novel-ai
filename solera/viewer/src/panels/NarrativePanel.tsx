import { useState } from "react";
import { proposeConceptFromNarrative } from "../api";
import type { Graph, Narrative } from "../types";
import {
  BulletSection,
  EmptyState,
  IntegrityBanner,
  MetaRow,
  Section,
  SectionTitle,
  StatusChip,
} from "./helpers";

export function NarrativeBody({
  graph,
  narrativeId,
  projectPath,
  onMutated,
}: {
  graph: Graph;
  narrativeId: string;
  projectPath: string;
  onMutated: () => void;
}) {
  const narrative = graph.narratives.find((n) => n.id === narrativeId);
  if (!narrative) return <EmptyState text="Narrative not found." />;

  const personas = graph.personas.filter((p) => narrative.about.includes(p.id));
  const journey = narrative.in_journey
    ? graph.journeys.find((j) => j.id === narrative.in_journey)
    : null;
  const proposedConcepts = graph.concepts.filter((c) =>
    narrative.proposes.includes(c.id),
  );

  return (
    <div className="space-y-4">
      <header>
        <h2 className="text-base font-semibold text-ink leading-snug">
          {narrative.statement || (
            <span className="italic text-slate-400">(no statement)</span>
          )}
        </h2>
        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-slate-400">
          <span className="font-mono">{narrative.id}</span>
          <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700">
            {narrative.form.replace("_", " ")}
          </span>
          <StatusChip status={narrative.status} />
          {narrative.integrity.length > 0 && (
            <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-semibold text-red-700 ring-1 ring-red-300">
              ⚠ integrity
            </span>
          )}
        </div>
      </header>
      {narrative.integrity.includes("missing_about") && (
        <IntegrityBanner
          title="This Narrative has no Persona."
          detail={
            <>
              A Narrative must declare at least one active Persona via{" "}
              <code>about:</code> in the frontmatter. Without it the Narrative
              is disconnected on the Service canvas.
            </>
          }
          repair={`/solera-write-narrative mode=update narrative_id=${narrative.id}`}
        />
      )}
      {narrative.integrity.includes("broken_in_journey_ref") && (
        <IntegrityBanner
          title={`in_journey "${narrative.in_journey}" does not exist.`}
          detail="The Journey referenced here is missing from the workspace. Either draw the Journey or update this Narrative to detach or point at an existing one."
          repair={`/solera-write-journey mode=create journey_id=${narrative.in_journey ?? ""}`}
        />
      )}
      <MetaRow
        label="About"
        value={
          personas.length > 0
            ? personas.map((p) => p.name).join(", ")
            : narrative.about.join(", ") || "(none)"
        }
      />
      {journey && <MetaRow label="In Journey" value={journey.name} />}
      <Section title="Context" body={narrative.context} />
      <BulletSection title="Acceptance Cues" items={narrative.acceptance_cues} />
      {proposedConcepts.length > 0 && (
        <div>
          <SectionTitle title="Proposed Concepts" tone="live" />
          <ul className="space-y-1 text-[12px] text-slate-700">
            {proposedConcepts.map((c) => (
              <li key={c.id}>
                <span className="font-mono text-[11px] text-slate-400">{c.id}</span>
                {" — "}
                {c.name}
                {c.intent.includes("needs human review") && (
                  <span className="ml-1 rounded-full bg-amber-50 px-1.5 py-0.5 text-[9px] font-medium text-amber-700">
                    intent needs review
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
      <ProposeAsConceptButton
        narrative={narrative}
        projectPath={projectPath}
        onMutated={onMutated}
      />
    </div>
  );
}

function ProposeAsConceptButton({
  narrative,
  projectPath,
  onMutated,
}: {
  narrative: Narrative;
  projectPath: string;
  onMutated: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [conceptId, setConceptId] = useState(slugify(narrative.id));
  const [conceptName, setConceptName] = useState(humanize(narrative.id));
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setOpen(false);
    setError(null);
    setSubmitting(false);
  };

  const submit = async () => {
    setSubmitting(true);
    setError(null);
    try {
      await proposeConceptFromNarrative(projectPath, {
        narrativeId: narrative.id,
        conceptId,
        conceptName,
      });
      onMutated();
      reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setSubmitting(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="w-full rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700"
      >
        Propose as Concept
      </button>
    );
  }

  return (
    <div className="space-y-3 rounded-md border border-emerald-200 bg-emerald-50/40 p-3">
      <div className="text-[11px] text-slate-600">
        Creates a <strong>stub Concept</strong>. Intent will be flagged{" "}
        <em>"needs human review"</em> — fill it via{" "}
        <code className="text-[11px]">solera-write-concept update</code>.
      </div>
      <label className="block text-[11px]">
        <span className="text-slate-500">Concept ID (kebab-case)</span>
        <input
          value={conceptId}
          onChange={(e) => setConceptId(e.target.value)}
          className="mt-1 w-full rounded border border-slate-300 px-2 py-1 font-mono text-[12px] focus:border-emerald-500 focus:outline-none"
          disabled={submitting}
        />
      </label>
      <label className="block text-[11px]">
        <span className="text-slate-500">Concept Name (human-readable)</span>
        <input
          value={conceptName}
          onChange={(e) => setConceptName(e.target.value)}
          className="mt-1 w-full rounded border border-slate-300 px-2 py-1 text-[12px] focus:border-emerald-500 focus:outline-none"
          disabled={submitting}
        />
      </label>
      {error && <div className="text-[11px] text-rose-600">{error}</div>}
      <div className="flex gap-2">
        <button
          onClick={submit}
          disabled={submitting || !conceptId.trim() || !conceptName.trim()}
          className={`flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-1.5 text-[12px] font-medium text-white transition disabled:bg-slate-300 ${
            submitting
              ? "cursor-wait bg-emerald-800"
              : "bg-emerald-600 hover:bg-emerald-700"
          }`}
          aria-busy={submitting}
        >
          {submitting && (
            <span
              aria-hidden
              className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-emerald-200 border-t-white"
            />
          )}
          <span>{submitting ? "Creating stub…" : "Create stub Concept"}</span>
        </button>
        <button
          onClick={reset}
          disabled={submitting}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-[12px] font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function slugify(id: string): string {
  return id
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function humanize(id: string): string {
  return id
    .split(/[-_]/)
    .filter(Boolean)
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join(" ");
}
