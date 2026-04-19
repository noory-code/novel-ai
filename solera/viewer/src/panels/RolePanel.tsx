import type { Graph } from "../types";
import {
  EmptyState,
  IntegrityBanner,
  MetaRow,
  Section,
  StatusChip,
  resolveName,
} from "./helpers";

export function RoleBody({ graph, roleId }: { graph: Graph; roleId: string }) {
  const role = graph.roles.find((r) => r.id === roleId);
  if (!role) return <EmptyState text="Role not found." />;

  const children = graph.roles.filter((r) => r.parent === role.id);
  const personas = graph.personas.filter((p) => p.role === role.id);
  const journeys = graph.journeys.filter((j) => j.walks === role.id);
  const narratives = graph.narratives.filter((n) => n.about_roles.includes(role.id));

  return (
    <div className="space-y-4">
      <header>
        <h2 className="text-lg font-semibold text-ink">{role.name}</h2>
        <div className="mt-0.5 flex items-center gap-2 text-[11px] text-slate-400">
          <span className="font-mono">{role.id}</span>
          <StatusChip status={role.status} />
          {role.integrity.length > 0 && (
            <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-semibold text-red-700 ring-1 ring-red-300">
              ⚠ integrity
            </span>
          )}
        </div>
      </header>
      {role.integrity.includes("broken_parent_ref") && (
        <IntegrityBanner
          title={`parent "${role.parent}" does not exist.`}
          detail="The parent Role referenced here is missing from the workspace. Either draw the parent Role or update this Role's `parent` to a known Role (or omit to make it top-level)."
          repair={`/solera-write-role mode=create role_id=${role.parent ?? ""}`}
        />
      )}
      {role.integrity.includes("inactive_parent_ref") && (
        <IntegrityBanner
          title={`parent "${role.parent}" is deprecated or archived.`}
          detail="Re-home this Role under an active parent, or promote it to top-level."
          repair={`/solera-write-role mode=update role_id=${role.id}`}
        />
      )}
      {role.parent && (
        <MetaRow label="Parent" value={resolveName(graph.roles, role.parent)} />
      )}
      {children.length > 0 && (
        <MetaRow label="Sub-roles" value={children.map((c) => c.name).join(", ")} />
      )}
      <Section title="Description" body={role.description} tone="north-star" />
      {role.context && <Section title="Context" body={role.context} />}
      {personas.length > 0 && (
        <MetaRow
          label="Personas"
          value={`${personas.length} archetype${personas.length === 1 ? "" : "s"}`}
        />
      )}
      {journeys.length > 0 && (
        <MetaRow
          label="Journeys"
          value={journeys.map((j) => j.name).join(", ")}
        />
      )}
      {narratives.length > 0 && (
        <MetaRow
          label="Narratives"
          value={`${narratives.length} about this Role`}
        />
      )}
    </div>
  );
}
