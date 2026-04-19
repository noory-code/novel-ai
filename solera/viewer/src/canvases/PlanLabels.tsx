import { useState } from "react";
import { createConcept, patchConcept } from "../api";
import { EditableText } from "../edit/EditableText";
import { EditableTextarea } from "../edit/EditableTextarea";
import type { Concept, WorkspaceLens } from "../types";

interface LabelContext {
  projectPath: string;
  onMutated: () => void;
}

// ---------------------------------------------------------------------------
// Concept label with inline edit
// ---------------------------------------------------------------------------

export function ConceptLabel({
  concept,
  lens,
  isRoot,
  projectPath,
  onMutated,
}: { concept: Concept; lens: WorkspaceLens; isRoot: boolean } & LabelContext) {
  const save = async (patch: Parameters<typeof patchConcept>[2]) => {
    await patchConcept(projectPath, concept.id, patch);
    onMutated();
  };

  // The Plan canvas uses a lens system: sketch/plan show current_design,
  // live shows current_shape. We edit whichever the user is currently
  // viewing, so the edit target tracks the lens naturally.
  const sub = lens === "live" ? concept.current_shape : concept.current_design;
  const subPatchKey =
    lens === "live" ? ("current_shape" as const) : ("current_design" as const);

  return (
    <div className="text-left nodrag nowheel">
      <div className="flex items-start justify-between gap-1">
        <EditableText
          value={concept.name}
          onSave={(name) => save({ name })}
          ariaLabel="Concept name"
          className={`font-semibold text-ink ${isRoot ? "text-[14px]" : "text-[12px]"}`}
          inputClassName={`w-full rounded border border-slate-300 bg-white px-1.5 py-0.5 ${isRoot ? "text-[14px]" : "text-[12px]"} font-semibold focus:border-indigo-600 focus:outline-none`}
        />
        <AddConceptButton
          parent={concept.id}
          title={`Child of ${concept.name}`}
          projectPath={projectPath}
          onMutated={onMutated}
        />
      </div>
      <EditableTextarea
        value={concept.intent}
        onSave={(intent) => save({ intent })}
        placeholder="(no intent — click to add)"
        ariaLabel="Concept intent"
        className="mt-0.5 text-[11px] italic text-slate-500 line-clamp-2 cursor-text"
        rows={3}
      />
      {sub && !sub.includes("no Stories") && (
        <EditableTextarea
          value={sub}
          onSave={(v) => save({ [subPatchKey]: v })}
          ariaLabel={subPatchKey === "current_shape" ? "Current Shape" : "Current Design"}
          className="mt-1 text-[11px] text-slate-700 line-clamp-2 cursor-text"
          rows={3}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Identity label + "+ concept" affordance (creates top-level Concepts)
// ---------------------------------------------------------------------------

export function IdentityConceptHubLabel({
  summary,
  projectPath,
  onMutated,
}: { summary: string } & LabelContext) {
  return (
    <div className="text-left nodrag nowheel">
      <div className="flex items-center justify-between gap-2">
        <div className="text-[10px] font-semibold uppercase tracking-widest text-amber-300">
          identity
        </div>
        <AddConceptButton
          title="Add top-level Concept"
          projectPath={projectPath}
          onMutated={onMutated}
          small
        />
      </div>
      <div className="mt-0.5 text-[14px] font-bold">BANAS</div>
      {summary && (
        <div className="mt-1 text-[11px] leading-tight text-slate-300 line-clamp-3">
          {summary}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Add Concept popover
// ---------------------------------------------------------------------------

function AddConceptButton({
  parent,
  title,
  projectPath,
  onMutated,
  small,
}: { parent?: string; title: string; small?: boolean } & LabelContext) {
  const [open, setOpen] = useState(false);
  const [idDraft, setIdDraft] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setOpen(false);
    setIdDraft("");
    setError(null);
    setSubmitting(false);
  };

  const submit = async () => {
    if (!idDraft.trim()) {
      setError("id required");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await createConcept(projectPath, {
        id: idDraft.trim(),
        name: idDraft.trim().replace(/-/g, " "),
        intent: "",
        current_design: "",
        current_shape: "(no Stories have contributed yet)",
        parent,
      });
      onMutated();
      reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setSubmitting(false);
    }
  };

  const btnClass = small
    ? "rounded bg-amber-400/20 px-1.5 py-0.5 text-[10px] font-semibold text-amber-300 hover:bg-amber-400/40"
    : "ml-1 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700 hover:bg-slate-200";

  return (
    <span className="relative nodrag">
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setOpen(!open);
        }}
        className={btnClass}
      >
        + concept
      </button>
      {open && (
        <div className="absolute right-0 top-6 z-50 w-56 rounded-md border border-slate-200 bg-white p-3 shadow-lg nodrag nowheel">
          <div className="mb-2 text-[11px] font-semibold text-slate-700">{title}</div>
          <label className="block text-[10px]">
            <span className="text-slate-500">id (kebab-case)</span>
            <input
              value={idDraft}
              onChange={(e) => setIdDraft(e.target.value)}
              placeholder="new-concept"
              className="mt-1 w-full rounded border border-slate-300 px-2 py-1 font-mono text-[11px] focus:border-indigo-600 focus:outline-none"
              autoFocus
              disabled={submitting}
              onKeyDown={(e) => {
                if (e.key === "Enter") submit();
                if (e.key === "Escape") reset();
              }}
            />
          </label>
          {error && <div className="mt-1 text-[10px] text-rose-700">⚠ {error}</div>}
          <div className="mt-2 flex gap-1">
            <button
              type="button"
              onClick={submit}
              disabled={submitting || !idDraft.trim()}
              className="flex-1 rounded bg-indigo-600 px-2 py-1 text-[11px] font-medium text-white hover:bg-indigo-700 disabled:bg-slate-300"
            >
              {submitting ? "Creating…" : "Create"}
            </button>
            <button
              type="button"
              onClick={reset}
              disabled={submitting}
              className="rounded border border-slate-300 px-2 py-1 text-[11px] text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </span>
  );
}
