import { useState } from "react";
import {
  createJourney,
  createNarrative,
  createPersona,
  createRole,
  patchJourney,
  patchNarrative,
  patchPersona,
  patchRole,
} from "../api";
import { EditableText } from "../edit/EditableText";
import { EditableTextarea } from "../edit/EditableTextarea";
import type { Journey, Narrative, Persona, Role } from "../types";

/**
 * Inline-editable label components for each canvas node kind.
 *
 * Every interactive control is marked with React Flow's ``nodrag`` /
 * ``nowheel`` classes so clicking into an input doesn't accidentally
 * start a node drag or a canvas zoom. Pan-through-label still works
 * outside the interactive zones.
 */

interface LabelContext {
  projectPath: string;
  onMutated: () => void;
}

// ---------------------------------------------------------------------------
// Role
// ---------------------------------------------------------------------------

export function RoleLabel({
  role,
  projectPath,
  onMutated,
}: { role: Role } & LabelContext) {
  const hasIntegrityIssue = role.integrity.length > 0;
  const save = async (patch: Parameters<typeof patchRole>[2]) => {
    await patchRole(projectPath, role.id, patch);
    onMutated();
  };
  return (
    <div className="flex flex-col gap-1 text-left nodrag nowheel">
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wide text-pink-600">Role</span>
        {hasIntegrityIssue && (
          <IntegrityChip flags={role.integrity} />
        )}
        {role.status !== "active" && (
          <span className="text-[10px] uppercase tracking-wide text-amber-700">
            {role.status}
          </span>
        )}
        <AddBelowRoleButton role={role} projectPath={projectPath} onMutated={onMutated} />
      </div>
      <EditableText
        value={role.name}
        onSave={(name) => save({ name })}
        ariaLabel="Role name"
        className="text-base font-semibold text-slate-800"
        inputClassName="w-full rounded border border-slate-300 bg-white px-1.5 py-0.5 text-base font-semibold focus:border-indigo-600 focus:outline-none"
      />
      <EditableTextarea
        value={role.description}
        onSave={(description) => save({ description })}
        placeholder="(no description — click to add)"
        ariaLabel="Role description"
        className="line-clamp-3 text-xs text-slate-700 cursor-text"
        textareaClassName="w-full rounded border border-slate-300 bg-white px-1.5 py-1 text-xs focus:border-indigo-600 focus:outline-none"
        rows={3}
      />
    </div>
  );
}

function AddBelowRoleButton({
  role,
  projectPath,
  onMutated,
}: { role: Role } & LabelContext) {
  return (
    <AddPopover
      label="+ add"
      title={`Add under ${role.name}`}
      items={[
        {
          key: "sub-role",
          label: "Sub-Role",
          description: "A more specific Role beneath this one",
          action: async (id) => {
            await createRole(projectPath, {
              id,
              name: id.replace(/-/g, " "),
              description: "",
              parent: role.id,
            });
          },
        },
        {
          key: "journey",
          label: "Journey this Role walks",
          description: "Sequence of steps this Role takes",
          action: async (id) => {
            await createJourney(projectPath, {
              id,
              walks: role.id,
              name: id.replace(/-/g, " "),
              trigger: "",
              outcome: "",
              steps: [],
            });
          },
        },
        {
          key: "persona",
          label: "Persona archetype under this Role",
          description: "A concrete named example of this Role",
          action: async (id) => {
            await createPersona(projectPath, {
              id,
              role: role.id,
              identity: "",
            });
          },
        },
        {
          key: "narrative",
          label: "Narrative about this Role",
          description: "As a / I want / so that — user story",
          action: async (id) => {
            await createNarrative(projectPath, {
              id,
              about_roles: [role.id],
              statement: "As a ..., I want ..., so that ...",
              context: "",
              acceptance_cues: [],
            });
          },
        },
      ]}
      onMutated={onMutated}
    />
  );
}

// ---------------------------------------------------------------------------
// Persona
// ---------------------------------------------------------------------------

export function PersonaLabel({
  persona,
  projectPath,
  onMutated,
}: { persona: Persona } & LabelContext) {
  const save = async (patch: Parameters<typeof patchPersona>[2]) => {
    await patchPersona(projectPath, persona.id, patch);
    onMutated();
  };
  return (
    <div className="flex flex-col gap-1 text-left nodrag nowheel">
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wide text-orange-600">
          Persona
        </span>
        {persona.integrity.length > 0 && <IntegrityChip flags={persona.integrity} />}
        {persona.status !== "active" && (
          <span className="text-[10px] uppercase tracking-wide text-amber-700">
            {persona.status}
          </span>
        )}
      </div>
      <EditableText
        value={persona.name}
        onSave={(name) => save({ name })}
        ariaLabel="Persona name"
        className="text-sm font-semibold text-slate-800"
        inputClassName="w-full rounded border border-slate-300 bg-white px-1.5 py-0.5 text-sm font-semibold focus:border-indigo-600 focus:outline-none"
      />
      <EditableTextarea
        value={persona.identity}
        onSave={(identity) => save({ identity })}
        placeholder="(no identity paragraph yet — click to add)"
        ariaLabel="Persona identity"
        className="line-clamp-2 text-xs text-slate-600 cursor-text"
        rows={3}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Journey
// ---------------------------------------------------------------------------

export function JourneyLabel({
  journey,
  orphan,
  projectPath,
  onMutated,
}: { journey: Journey; orphan: boolean } & LabelContext) {
  const hasIntegrityIssue = journey.integrity.length > 0 || orphan;
  const save = async (patch: Parameters<typeof patchJourney>[2]) => {
    await patchJourney(projectPath, journey.id, patch);
    onMutated();
  };
  return (
    <div className="flex flex-col gap-1 text-left nodrag nowheel">
      <div className="flex items-center gap-2">
        <span className="text-[10px] uppercase tracking-wide text-blue-600">Journey</span>
        {hasIntegrityIssue && <IntegrityChip flags={journey.integrity} orphan={orphan} />}
        {journey.status !== "active" && (
          <span className="text-[10px] uppercase tracking-wide text-amber-700">
            {journey.status}
          </span>
        )}
        <AddNarrativeInJourneyButton
          journey={journey}
          projectPath={projectPath}
          onMutated={onMutated}
        />
      </div>
      <EditableText
        value={journey.name}
        onSave={(name) => save({ name })}
        ariaLabel="Journey name"
        className="text-base font-semibold text-slate-800"
        inputClassName="w-full rounded border border-slate-300 bg-white px-1.5 py-0.5 text-base font-semibold focus:border-indigo-600 focus:outline-none"
      />
      <div className="text-xs text-slate-600">
        <span className="text-slate-400">Trigger: </span>
        <EditableTextarea
          value={journey.trigger}
          onSave={(trigger) => save({ trigger })}
          placeholder="(no trigger — click to add)"
          ariaLabel="Journey trigger"
          className="inline line-clamp-2 cursor-text"
          rows={2}
        />
      </div>
      <div className="text-xs text-slate-600">
        <span className="text-slate-400">Outcome: </span>
        <EditableTextarea
          value={journey.outcome}
          onSave={(outcome) => save({ outcome })}
          placeholder="(no outcome — click to add)"
          ariaLabel="Journey outcome"
          className="inline line-clamp-2 cursor-text"
          rows={2}
        />
      </div>
      <div className="mt-1 text-[11px] text-slate-500">
        {journey.steps.length} step{journey.steps.length === 1 ? "" : "s"}
        {journey.walks && (
          <span className="text-slate-400"> · walks {journey.walks}</span>
        )}
      </div>
    </div>
  );
}

function AddNarrativeInJourneyButton({
  journey,
  projectPath,
  onMutated,
}: { journey: Journey } & LabelContext) {
  if (!journey.walks) return null;
  return (
    <AddPopover
      label="+ narrative"
      title={`Add Narrative in ${journey.name}`}
      items={[
        {
          key: "narrative",
          label: "Narrative in_journey",
          description: "User story anchored to this Journey",
          action: async (id) => {
            await createNarrative(projectPath, {
              id,
              about_roles: [journey.walks],
              in_journey: journey.id,
              statement: "As a ..., I want ..., so that ...",
              context: "",
              acceptance_cues: [],
            });
          },
        },
      ]}
      onMutated={onMutated}
    />
  );
}

// ---------------------------------------------------------------------------
// Narrative
// ---------------------------------------------------------------------------

export function NarrativeLabel({
  narrative,
  projectPath,
  onMutated,
}: { narrative: Narrative } & LabelContext) {
  const formColor =
    narrative.form === "jtbd"
      ? "text-violet-600"
      : narrative.form === "scenario"
        ? "text-teal-600"
        : "text-emerald-600";
  const save = async (patch: Parameters<typeof patchNarrative>[2]) => {
    await patchNarrative(projectPath, narrative.id, patch);
    onMutated();
  };
  return (
    <div className="flex flex-col gap-1 text-left nodrag nowheel">
      <div className="flex items-center gap-2">
        <span className={`text-[10px] uppercase tracking-wide ${formColor}`}>
          {narrative.form.replace("_", " ")}
        </span>
        {narrative.integrity.length > 0 && <IntegrityChip flags={narrative.integrity} />}
        {narrative.status !== "active" && (
          <span className="text-[10px] uppercase tracking-wide text-amber-700">
            {narrative.status}
          </span>
        )}
      </div>
      <EditableTextarea
        value={narrative.statement}
        onSave={(statement) => save({ statement })}
        placeholder="(empty — click to add the As a / I want / so that statement)"
        ariaLabel="Narrative statement"
        className="line-clamp-3 text-xs italic leading-snug text-slate-700 cursor-text"
        rows={3}
      />
      {narrative.proposes.length > 0 && (
        <div className="mt-1 text-[11px] text-emerald-700">
          → proposes {narrative.proposes.length} Concept
          {narrative.proposes.length === 1 ? "" : "s"}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Identity label — static render (centre hub) + "+ new Role" button.
// ---------------------------------------------------------------------------

export function IdentityLabelWithCreate({
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
        <AddPopover
          label="+ role"
          title="Add top-level Role"
          buttonClassName="rounded bg-amber-400/20 px-1.5 py-0.5 text-[10px] font-semibold text-amber-300 hover:bg-amber-400/40"
          items={[
            {
              key: "role",
              label: "Top-level Role",
              description: "admin / fan / hero / 3rd-party / …",
              action: async (id) => {
                await createRole(projectPath, {
                  id,
                  name: id.replace(/-/g, " "),
                  description: "",
                });
              },
            },
          ]}
          onMutated={onMutated}
        />
      </div>
      {summary && (
        <div className="mt-1 text-[12px] leading-tight text-slate-200 line-clamp-3">
          {summary}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Shared helpers
// ---------------------------------------------------------------------------

interface AddPopoverItem {
  key: string;
  label: string;
  description: string;
  action: (id: string) => Promise<void>;
}

function AddPopover({
  label,
  title,
  items,
  onMutated,
  buttonClassName,
}: {
  label: string;
  title: string;
  items: AddPopoverItem[];
  onMutated: () => void;
  buttonClassName?: string;
}) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<AddPopoverItem | null>(null);
  const [idDraft, setIdDraft] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = () => {
    setOpen(false);
    setSelected(null);
    setIdDraft("");
    setError(null);
    setSubmitting(false);
  };

  const submit = async () => {
    if (!selected) return;
    if (!idDraft.trim()) {
      setError("id required");
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await selected.action(idDraft.trim());
      onMutated();
      reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setSubmitting(false);
    }
  };

  return (
    <span className="relative nodrag">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={
          buttonClassName ??
          "ml-auto rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700 hover:bg-slate-200"
        }
      >
        {label}
      </button>
      {open && (
        <div className="absolute right-0 top-6 z-50 w-64 rounded-md border border-slate-200 bg-white p-3 shadow-lg nodrag nowheel">
          <div className="mb-2 text-[11px] font-semibold text-slate-700">
            {title}
          </div>
          {!selected && (
            <div className="space-y-1">
              {items.map((item) => (
                <button
                  key={item.key}
                  type="button"
                  onClick={() => setSelected(item)}
                  className="block w-full rounded px-2 py-1 text-left text-[11px] hover:bg-slate-100"
                >
                  <div className="font-medium text-slate-800">{item.label}</div>
                  <div className="text-[10px] text-slate-500">{item.description}</div>
                </button>
              ))}
              <button
                type="button"
                onClick={reset}
                className="mt-2 w-full rounded border border-slate-200 px-2 py-1 text-[10px] text-slate-500 hover:bg-slate-50"
              >
                Cancel
              </button>
            </div>
          )}
          {selected && (
            <div className="space-y-2">
              <div className="text-[10px] text-slate-500">
                Creating: <span className="text-slate-700">{selected.label}</span>
              </div>
              <label className="block text-[10px]">
                <span className="text-slate-500">id (kebab-case)</span>
                <input
                  value={idDraft}
                  onChange={(e) => setIdDraft(e.target.value)}
                  placeholder="my-new-thing"
                  className="mt-1 w-full rounded border border-slate-300 px-2 py-1 font-mono text-[11px] focus:border-indigo-600 focus:outline-none"
                  autoFocus
                  disabled={submitting}
                />
              </label>
              {error && (
                <div className="text-[10px] text-rose-700">⚠ {error}</div>
              )}
              <div className="flex gap-1">
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
        </div>
      )}
    </span>
  );
}

function IntegrityChip({ flags, orphan }: { flags: string[]; orphan?: boolean }) {
  let label = "issue";
  if (flags.includes("missing_role")) label = "no role";
  else if (flags.includes("broken_role_ref")) label = "unknown role";
  else if (flags.includes("missing_walks")) label = "no walks";
  else if (flags.includes("broken_walks_ref")) label = "unknown role (walks)";
  else if (flags.includes("missing_about_roles")) label = "no roles";
  else if (flags.includes("broken_about_role_ref")) label = "unknown role";
  else if (flags.includes("broken_about_persona_ref")) label = "unknown persona";
  else if (flags.includes("broken_in_journey_ref")) label = "unknown journey";
  else if (flags.includes("legacy_about_field")) label = "legacy v4 data";
  else if (flags.includes("broken_parent_ref")) label = "unknown parent";
  else if (flags.includes("inactive_parent_ref")) label = "inactive parent";
  else if (orphan) label = "orphan";
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700 ring-1 ring-red-300">
      <span aria-hidden>⚠</span>
      <span>{label}</span>
    </span>
  );
}
