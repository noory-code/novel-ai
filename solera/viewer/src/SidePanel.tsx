import { useState } from "react";
import { patchConcept, proposeConceptFromNarrative } from "./api";
import type { SelectedNode } from "./canvases/PlanCanvas";
import { MarkdownBody } from "./MarkdownBody";
import type {
  BranchSide,
  Concept,
  Graph,
  Identity,
  Layout,
  Narrative,
} from "./types";

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

function IdentityBody({ identity }: { identity: Identity }) {
  return (
    <div className="space-y-5">
      <Section title="Mission" body={identity.mission} />
      <Section title="Vision" body={identity.vision} />
      <Section title="Core Values" body={identity.values} />
      <Section title="Tone & Manner" body={identity.tone_and_manner} />
      <Section title="Goals" body={identity.goals} />
      {Object.entries(identity.extras ?? {}).map(([key, body]) => (
        <Section key={key} title={humanizeStem(key)} body={body} />
      ))}
    </div>
  );
}

function humanizeStem(stem: string): string {
  return stem
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function ConceptBody({
  graph,
  conceptId,
  projectPath,
  layout,
  onMutated,
  onLayoutChange,
}: {
  graph: Graph;
  conceptId: string;
  projectPath: string;
  layout: Layout;
  onMutated: () => void;
  onLayoutChange: (next: Layout) => void;
}) {
  const concept = graph.concepts.find((c) => c.id === conceptId);
  if (!concept) return <EmptyState text="Concept not found." />;

  const children = graph.concepts.filter((c) => c.parent === concept.id);
  const isTopLevel = !concept.parent || !graph.concepts.some((c) => c.id === concept.parent);

  return (
    <div className="space-y-4">
      <header>
        <h2 className="text-lg font-semibold text-ink">{concept.name}</h2>
        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-slate-400">
          <span className="font-mono">{concept.id}</span>
          <StatusChip status={concept.status} />
        </div>
      </header>
      <ParentSelect
        graph={graph}
        concept={concept}
        projectPath={projectPath}
        onMutated={onMutated}
      />
      {isTopLevel && (
        <SideToggle
          conceptId={concept.id}
          layout={layout}
          onLayoutChange={onLayoutChange}
        />
      )}
      {children.length > 0 && (
        <MetaRow label="Children" value={children.map((c) => c.name).join(", ")} />
      )}
      <Section title="Intent" body={concept.intent} tone="north-star" />
      <Section title="Current Design" body={concept.current_design} tone="sketch" />
      <Section title="Current Shape" body={concept.current_shape} tone="live" />
      {concept.horizon && <Section title="Horizon" body={concept.horizon} />}
    </div>
  );
}

function SideToggle({
  conceptId,
  layout,
  onLayoutChange,
}: {
  conceptId: string;
  layout: Layout;
  onLayoutChange: (next: Layout) => void;
}) {
  const nodeKey = `concept:${conceptId}`;
  const current: BranchSide = layout.nodes[nodeKey]?.side ?? "right";

  const setSide = (next: BranchSide) => {
    if (next === current) return;
    // Drop x/y on this node AND all its descendants so the fresh bilateral
    // auto-layout can place them on the new side. Keep the `side` hint.
    const nextNodes = { ...layout.nodes };
    const prior = layout.nodes[nodeKey] ?? {};
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { x: _px, y: _py, ...rest } = prior;
    nextNodes[nodeKey] = { ...rest, side: next };
    onLayoutChange({ ...layout, nodes: nextNodes });
  };

  return (
    <div className="flex items-start gap-3 text-[12px]">
      <span className="mt-1 w-16 shrink-0 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
        Side
      </span>
      <div className="flex gap-1 rounded-md bg-slate-100 p-0.5">
        <SideButton active={current === "left"} onClick={() => setSide("left")}>
          ← Left
        </SideButton>
        <SideButton active={current === "right"} onClick={() => setSide("right")}>
          Right →
        </SideButton>
      </div>
    </div>
  );
}

function SideButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded px-2.5 py-1 text-[11px] font-medium transition ${
        active ? "bg-white text-ink shadow-sm" : "text-slate-500 hover:text-slate-800"
      }`}
    >
      {children}
    </button>
  );
}

function ParentSelect({
  graph,
  concept,
  projectPath,
  onMutated,
}: {
  graph: Graph;
  concept: Concept;
  projectPath: string;
  onMutated: () => void;
}) {
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Avoid listing descendants to prevent cycles on the client too.
  const descendantIds = collectDescendants(concept.id, graph.concepts);
  const options = graph.concepts.filter(
    (c) => c.id !== concept.id && !descendantIds.has(c.id),
  );

  const onChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    const nextParent = value === "__none__" ? null : value;
    if (nextParent === concept.parent) return;
    setSaving(true);
    setError(null);
    try {
      await patchConcept(projectPath, concept.id, { parent: nextParent });
      onMutated();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex items-start gap-3 text-[12px]">
      <span className="mt-1 w-16 shrink-0 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
        Parent
      </span>
      <div className="flex-1">
        <select
          value={concept.parent ?? "__none__"}
          onChange={onChange}
          disabled={saving}
          className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-[12px] focus:border-sketch focus:outline-none"
        >
          <option value="__none__">— (top-level surface)</option>
          {options.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        {error && <div className="mt-1 text-[11px] text-rose-500">{error}</div>}
      </div>
    </div>
  );
}

function collectDescendants(id: string, concepts: Concept[]): Set<string> {
  const out = new Set<string>();
  const visit = (parentId: string) => {
    for (const c of concepts) {
      if (c.parent === parentId && !out.has(c.id)) {
        out.add(c.id);
        visit(c.id);
      }
    }
  };
  visit(id);
  return out;
}

function Section({
  title,
  body,
  tone,
}: {
  title: string;
  body: string | null;
  tone?: "north-star" | "sketch" | "live";
}) {
  if (body === null || body.trim() === "") {
    return (
      <div>
        <SectionTitle title={title} tone={tone} />
        <p className="text-[12px] italic text-slate-400">not set</p>
      </div>
    );
  }
  return (
    <div>
      <SectionTitle title={title} tone={tone} />
      <MarkdownBody text={body} />
    </div>
  );
}

function SectionTitle({
  title,
  tone,
}: {
  title: string;
  tone?: "north-star" | "sketch" | "live";
}) {
  const toneClass =
    tone === "north-star"
      ? "text-amber-600"
      : tone === "sketch"
        ? "text-sketch"
        : tone === "live"
          ? "text-live"
          : "text-slate-500";
  return (
    <div className={`mb-1 text-[10px] font-semibold uppercase tracking-widest ${toneClass}`}>
      {title}
    </div>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3 text-[12px]">
      <span className="w-16 shrink-0 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
        {label}
      </span>
      <span className="text-slate-700">{value}</span>
    </div>
  );
}

function StatusChip({ status }: { status: string }) {
  const color =
    status === "active"
      ? "bg-emerald-50 text-emerald-700"
      : status === "deprecated"
        ? "bg-rose-50 text-rose-700"
        : "bg-slate-100 text-slate-600";
  return (
    <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${color}`}>{status}</span>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="text-sm italic text-slate-400">{text}</p>;
}

// ---------------------------------------------------------------------------
// v4 Living-axis body components (Persona, Journey, Narrative)
// ---------------------------------------------------------------------------

function PersonaBody({ graph, personaId }: { graph: Graph; personaId: string }) {
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

function JourneyBody({ graph, journeyId }: { graph: Graph; journeyId: string }) {
  const journey = graph.journeys.find((j) => j.id === journeyId);
  if (!journey) return <EmptyState text="Journey not found." />;

  const persona = graph.personas.find((p) => p.id === journey.walks);
  const narratives = graph.narratives.filter((n) => n.in_journey === journey.id);

  return (
    <div className="space-y-4">
      <header>
        <h2 className="text-lg font-semibold text-ink">{journey.name}</h2>
        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-slate-400">
          <span className="font-mono">{journey.id}</span>
          <StatusChip status={journey.status} />
          {!persona && journey.walks && (
            <span className="rounded-full bg-orange-50 px-2 py-0.5 text-[10px] font-medium text-orange-700">
              ⚠ orphan
            </span>
          )}
        </div>
      </header>
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

function NarrativeBody({
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
        </div>
      </header>
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
          className="flex-1 rounded-md bg-emerald-600 px-3 py-1.5 text-[12px] font-medium text-white hover:bg-emerald-700 disabled:bg-slate-300"
        >
          {submitting ? "creating…" : "Create stub Concept"}
        </button>
        <button
          onClick={reset}
          disabled={submitting}
          className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-[12px] font-medium text-slate-600 hover:bg-slate-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

function BulletSection({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) {
    return (
      <div>
        <SectionTitle title={title} />
        <p className="text-[12px] italic text-slate-400">(none)</p>
      </div>
    );
  }
  return (
    <div>
      <SectionTitle title={title} />
      <ul className="list-disc space-y-1 pl-4 text-[12px] text-slate-700">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function resolveName<T extends { id: string; name: string }>(
  list: T[],
  id: string,
): string {
  const found = list.find((x) => x.id === id);
  return found ? found.name : id;
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
