import type { Identity } from "../types";
import { Section } from "./helpers";

export function IdentityBody({ identity }: { identity: Identity }) {
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
