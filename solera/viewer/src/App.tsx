import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  fetchGraph,
  fetchLayout,
  openGraphSocket,
  resolveProjectPath,
  saveLayout,
  type SocketStatus,
} from "./api";
import { PlanCanvas, type SelectedNode } from "./canvases/PlanCanvas";
import { ActorsCanvas } from "./canvases/ActorsCanvas";
import { SidePanel } from "./SidePanel";
import type { Graph, Layout, WorkspaceLens } from "./types";

type SaveState = "idle" | "saving" | "saved" | "error";

export function App() {
  const projectPath = useMemo(resolveProjectPath, []);
  const [graph, setGraph] = useState<Graph | null>(null);
  const [layout, setLayout] = useState<Layout>({ nodes: {} });
  const [error, setError] = useState<string | null>(null);
  const [lens, setLens] = useState<WorkspaceLens>("plan");
  const [selection, setSelection] = useState<SelectedNode | null>(null);
  const [socketStatus, setSocketStatus] = useState<SocketStatus>("connecting");
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const saveTimer = useRef<number | null>(null);
  const savedTimer = useRef<number | null>(null);

  const reload = useCallback(async () => {
    if (!projectPath) return;
    try {
      const [g, l] = await Promise.all([fetchGraph(projectPath), fetchLayout(projectPath)]);
      setGraph(g);
      setLayout(l);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [projectPath]);

  const reloadLayoutOnly = useCallback(async () => {
    if (!projectPath) return;
    try {
      const l = await fetchLayout(projectPath);
      setLayout(l);
    } catch (err) {
      // Layout reload failures are non-fatal — the graph is still consistent.
      setError(err instanceof Error ? err.message : String(err));
    }
  }, [projectPath]);

  useEffect(() => {
    void reload();
  }, [reload]);

  useEffect(() => {
    if (!projectPath) return;
    const sock = openGraphSocket(projectPath, {
      onEvent: (msg) => {
        if (msg.event === "graph_changed") {
          void reload();
        } else if (msg.event === "layout_changed") {
          // Layout-only event → skip full graph re-fetch. This keeps canvas
          // selection and side-panel state alive when the user drags a node
          // (which triggers a save, which the watcher sees and broadcasts).
          void reloadLayoutOnly();
        }
      },
      onStatus: setSocketStatus,
      onError: (err) => setError(err),
    });
    return () => sock.close();
  }, [projectPath, reload, reloadLayoutOnly]);

  const persistLayout = useCallback(
    (next: Layout) => {
      setLayout(next);
      if (!projectPath) return;
      if (saveTimer.current !== null) {
        window.clearTimeout(saveTimer.current);
      }
      setSaveState("saving");
      saveTimer.current = window.setTimeout(() => {
        saveTimer.current = null;
        saveLayout(projectPath, next)
          .then(() => {
            setSaveState("saved");
            if (savedTimer.current !== null) window.clearTimeout(savedTimer.current);
            savedTimer.current = window.setTimeout(() => setSaveState("idle"), 1500);
          })
          .catch((err) => {
            setSaveState("error");
            setError(err instanceof Error ? err.message : String(err));
          });
      }, 400);
    },
    [projectPath],
  );

  if (!projectPath) {
    return (
      <div className="flex h-full items-center justify-center p-8 text-center">
        <div>
          <h1 className="mb-2 text-2xl font-semibold">Solera Map</h1>
          <p className="text-slate-500">
            Add <code>?project_path=/absolute/path/to/project</code> to the URL.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <Header
        lens={lens}
        onLensChange={setLens}
        projectPath={projectPath}
        error={error}
        socketStatus={socketStatus}
        saveState={saveState}
      />
      <main className="flex flex-1 overflow-hidden">
        <div className="flex-1">
          {graph ? (
            // Lens-routed canvas switch. `service` is its own component (the
            // 4th canvas added in v0.1.0). `plan`/`build`/`live` still share
            // PlanCanvas with lens-driven styling — promoting them to dedicated
            // components is left to a future PR.
            lens === "actors" ? (
              <ActorsCanvas
                graph={graph}
                layout={layout}
                onLayoutChange={persistLayout}
                onSelect={setSelection}
                selection={selection}
              />
            ) : (
              <PlanCanvas
                graph={graph}
                lens={lens}
                layout={layout}
                onLayoutChange={persistLayout}
                onSelect={setSelection}
                selection={selection}
              />
            )
          ) : (
            <LoadingScreen />
          )}
        </div>
        {graph && (
          <SidePanel
            graph={graph}
            selection={selection}
            projectPath={projectPath}
            layout={layout}
            onClose={() => setSelection(null)}
            onMutated={() => void reload()}
            onLayoutChange={persistLayout}
          />
        )}
      </main>
    </div>
  );
}

interface HeaderProps {
  lens: WorkspaceLens;
  onLensChange: (lens: WorkspaceLens) => void;
  projectPath: string;
  error: string | null;
  socketStatus: SocketStatus;
  saveState: SaveState;
}

function Header({
  lens,
  onLensChange,
  projectPath,
  error,
  socketStatus,
  saveState,
}: HeaderProps) {
  const tabs: { key: WorkspaceLens; label: string; accent: string }[] = [
    // Each lens is rendered in the darker 700-shade of its palette so the
    // active-tab label clears WCAG AA (4.5:1) on the white tab background.
    // The lighter tokens (`sketch`, `paint`, `live`, `rose-500`) remain for
    // decorative surfaces (borders, backgrounds) where contrast isn't gating.
    { key: "actors", label: "Actors", accent: "text-rose-700" },
    { key: "plan", label: "Plan", accent: "text-indigo-700" },
    { key: "build", label: "Build", accent: "text-amber-700" },
    { key: "live", label: "Live", accent: "text-emerald-700" },
  ];
  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white/80 px-4 py-2 backdrop-blur">
      <div className="flex items-center gap-4">
        <span className="text-sm font-semibold tracking-wide">SOLERA MAP</span>
        <span className="font-mono text-xs text-slate-500" title={projectPath}>
          {truncateMiddle(projectPath, 48)}
        </span>
      </div>
      <nav className="flex gap-1 rounded-lg bg-slate-100 p-1">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => onLensChange(t.key)}
            className={`rounded-md px-3 py-1 text-sm font-medium transition ${
              lens === t.key
                ? `bg-white shadow-sm ${t.accent}`
                : "text-slate-700 hover:text-slate-900"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <div className="flex w-64 items-center justify-end gap-2 text-right text-xs">
        <SaveIndicator state={saveState} />
        <SocketIndicator status={socketStatus} />
        {error && (
          <span className="truncate text-rose-600" title={error} aria-label="connection error">
            {error}
          </span>
        )}
      </div>
    </header>
  );
}

function SaveIndicator({ state }: { state: SaveState }) {
  if (state === "idle") return null;
  const label = {
    saving: "saving…",
    saved: "saved",
    error: "save failed",
  }[state];
  const tone = {
    saving: "text-slate-500",
    saved: "text-emerald-700",
    error: "text-rose-700",
  }[state];
  return (
    <span className={`inline-flex items-center gap-1 ${tone}`} role="status" aria-live="polite">
      {state === "saving" && <Spinner small />}
      <span>{label}</span>
    </span>
  );
}

function SocketIndicator({ status }: { status: SocketStatus }) {
  const label = {
    connecting: "connecting…",
    connected: "live",
    reconnecting: "reconnecting…",
    disconnected: "offline",
  }[status];
  const dot = {
    connecting: "bg-amber-500 animate-pulse",
    connected: "bg-emerald-500",
    reconnecting: "bg-amber-500 animate-pulse",
    disconnected: "bg-slate-400",
  }[status];
  const tone = {
    connecting: "text-amber-700",
    connected: "text-emerald-700",
    reconnecting: "text-amber-700",
    disconnected: "text-slate-600",
  }[status];
  return (
    <span
      className={`inline-flex items-center gap-1 ${tone}`}
      title={`Server connection: ${label}`}
      aria-label={`Server connection: ${label}`}
    >
      <span aria-hidden className={`h-2 w-2 rounded-full ${dot}`} />
      <span>{label}</span>
    </span>
  );
}

function LoadingScreen() {
  return (
    <div
      className="flex h-full flex-col items-center justify-center gap-3 text-slate-600"
      role="status"
      aria-live="polite"
    >
      <Spinner />
      <div className="text-sm">Loading graph…</div>
    </div>
  );
}

function Spinner({ small = false }: { small?: boolean }) {
  const size = small ? "h-3 w-3 border-2" : "h-6 w-6 border-[3px]";
  return (
    <span
      aria-hidden
      className={`inline-block ${size} animate-spin rounded-full border-slate-300 border-t-slate-700`}
    />
  );
}

function truncateMiddle(s: string, max: number): string {
  if (s.length <= max) return s;
  const side = Math.floor((max - 1) / 2);
  return `${s.slice(0, side)}…${s.slice(-side)}`;
}
