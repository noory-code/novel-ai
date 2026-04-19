import { useState } from "react";
import { patchConcept } from "../api";
import type { BranchSide, Concept, Graph, Layout } from "../types";
import { EmptyState, MetaRow, Section, StatusChip } from "./helpers";

export function ConceptBody({
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
        active ? "bg-white text-ink shadow-sm" : "text-slate-700 hover:text-slate-900"
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
  const [pendingParent, setPendingParent] = useState<string | null>(null);
  // Parent id of the last failed attempt — stays disabled until the user
  // retries or reverts, so accidental rapid-fire of the same broken change is
  // blocked even though the dropdown itself would otherwise be re-enabled.
  const [failedAttempt, setFailedAttempt] = useState<{ parent: string | null } | null>(
    null,
  );

  // Avoid listing descendants to prevent cycles on the client too.
  const descendantIds = collectDescendants(concept.id, graph.concepts);
  const options = graph.concepts.filter(
    (c) => c.id !== concept.id && !descendantIds.has(c.id),
  );

  const submit = async (nextParent: string | null) => {
    setSaving(true);
    setError(null);
    setPendingParent(nextParent);
    try {
      await patchConcept(projectPath, concept.id, { parent: nextParent });
      setFailedAttempt(null);
      onMutated();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setFailedAttempt({ parent: nextParent });
    } finally {
      setSaving(false);
      setPendingParent(null);
    }
  };

  const onChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    const nextParent = value === "__none__" ? null : value;
    if (nextParent === concept.parent) return;
    void submit(nextParent);
  };

  const locked =
    saving || (failedAttempt !== null && failedAttempt.parent === (pendingParent ?? null));

  return (
    <div className="flex items-start gap-3 text-[12px]">
      <span className="mt-1 w-16 shrink-0 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
        Parent
      </span>
      <div className="flex-1">
        <select
          value={concept.parent ?? "__none__"}
          onChange={onChange}
          disabled={locked}
          className={`w-full rounded border bg-white px-2 py-1 text-[12px] focus:outline-none ${
            failedAttempt
              ? "border-rose-400 focus:border-rose-500"
              : "border-slate-300 focus:border-sketch"
          }`}
          aria-invalid={failedAttempt ? true : undefined}
        >
          <option value="__none__">— (top-level surface)</option>
          {options.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        {saving && (
          <div
            className="mt-1 inline-flex items-center gap-1 text-[11px] text-slate-500"
            role="status"
            aria-live="polite"
          >
            <span
              aria-hidden
              className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600"
            />
            <span>saving parent…</span>
          </div>
        )}
        {error && (
          <div className="mt-1 flex items-center gap-2 text-[11px] text-rose-700">
            <span>⚠ {error}</span>
            {failedAttempt && (
              <button
                type="button"
                onClick={() => void submit(failedAttempt.parent)}
                className="rounded bg-rose-100 px-2 py-0.5 text-[10px] font-semibold text-rose-700 hover:bg-rose-200"
              >
                retry
              </button>
            )}
          </div>
        )}
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
