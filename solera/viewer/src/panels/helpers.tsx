import { useState } from "react";
import { MarkdownBody } from "../MarkdownBody";

// ---------------------------------------------------------------------------
// Shared side-panel UI atoms.
//
// These helpers were previously co-located inside SidePanel.tsx; as the file
// grew past 500 LOC they needed their own home. Each panel (Identity /
// Concept / Persona / Journey / Narrative) composes these primitives.
// ---------------------------------------------------------------------------

export type SectionTone = "north-star" | "sketch" | "live";

export function Section({
  title,
  body,
  tone,
}: {
  title: string;
  body: string | null;
  tone?: SectionTone;
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

export function SectionTitle({ title, tone }: { title: string; tone?: SectionTone }) {
  // 10px uppercase bold labels need ≥4.5:1 contrast (small text per WCAG AA).
  // The lighter custom tokens (`sketch`, `live`) and `amber-600` fail on
  // white, so the tone variants use Tailwind's 700-shades here.
  const toneClass =
    tone === "north-star"
      ? "text-amber-700"
      : tone === "sketch"
        ? "text-indigo-700"
        : tone === "live"
          ? "text-emerald-700"
          : "text-slate-600";
  return (
    <div className={`mb-1 text-[10px] font-semibold uppercase tracking-widest ${toneClass}`}>
      {title}
    </div>
  );
}

export function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex gap-3 text-[12px]">
      <span className="w-16 shrink-0 text-[10px] font-semibold uppercase tracking-widest text-slate-400">
        {label}
      </span>
      <span className="text-slate-700">{value}</span>
    </div>
  );
}

export function StatusChip({ status }: { status: string }) {
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

export function EmptyState({ text }: { text: string }) {
  return <p className="text-sm italic text-slate-400">{text}</p>;
}

export function BulletSection({ title, items }: { title: string; items: string[] }) {
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

export function IntegrityBanner({
  title,
  detail,
  repair,
}: {
  title: string;
  detail: React.ReactNode;
  repair: string;
}) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    void navigator.clipboard.writeText(repair).then(
      () => {
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      },
      () => {
        // Clipboard denied: fall back to selecting — the user can still copy
        // manually. Swallow the rejection rather than throw.
      },
    );
  };
  return (
    <div className="space-y-2 rounded-md border border-red-300 bg-red-50 p-3 text-[12px] text-red-900">
      <div className="flex items-center gap-2">
        <span aria-hidden className="text-base">
          ⚠
        </span>
        <strong className="font-semibold">{title}</strong>
      </div>
      <p className="text-red-800">{detail}</p>
      <div className="flex items-center gap-2 rounded border border-red-200 bg-white px-2 py-1 font-mono text-[11px] text-red-800">
        <span className="flex-1 select-all break-all">{repair}</span>
        <button
          onClick={copy}
          className="rounded bg-red-100 px-2 py-0.5 text-[10px] font-semibold text-red-700 hover:bg-red-200"
          type="button"
        >
          {copied ? "copied" : "copy"}
        </button>
      </div>
    </div>
  );
}

export function resolveName<T extends { id: string; name: string }>(
  list: T[],
  id: string,
): string {
  const found = list.find((x) => x.id === id);
  return found ? found.name : id;
}
