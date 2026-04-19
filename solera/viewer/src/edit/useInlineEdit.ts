import { useCallback, useRef, useState } from "react";

export type InlineEditStatus = "idle" | "editing" | "saving" | "error";

export interface InlineEditState<T> {
  status: InlineEditStatus;
  /** The value currently showing in the editor (committed or in-flight). */
  draft: T;
  /** Error message from the most recent failed save (cleared on next edit). */
  error: string | null;
}

export interface InlineEditActions<T> {
  beginEdit: () => void;
  updateDraft: (next: T) => void;
  /** Commit the draft by calling ``save``; returns a promise that resolves
   *  to true on success, false on failure. */
  commit: () => Promise<boolean>;
  cancel: () => void;
}

export interface UseInlineEditArgs<T> {
  /** Current committed value rendered when not editing. */
  value: T;
  /** Save function — called on commit with the current draft. Must throw on
   *  failure (rejected promise). The inline-edit hook catches and surfaces
   *  the error without bubbling it further. */
  save: (next: T) => Promise<void>;
  /** Optional equality override (for arrays/objects where ``===`` is wrong).
   *  Default is strict equality. */
  equals?: (a: T, b: T) => boolean;
}

/**
 * Tiny state machine for "click to edit this field" UX.
 *
 *   idle ──beginEdit──▶ editing ──cancel──▶ idle
 *                          │
 *                        commit
 *                          │
 *                          ▼
 *                        saving ──success──▶ idle
 *                          │
 *                        error (user can retry, cancel, or keep editing)
 *
 * The hook tracks a local ``draft`` so the user's typed-but-unsaved input
 * isn't clobbered by a concurrent ``value`` change (e.g. a WebSocket graph
 * refresh). A successful save returns the hook to ``idle`` with
 * ``draft === value``; a failure stays in ``editing`` with the draft
 * intact and an ``error`` message ready to display.
 */
export function useInlineEdit<T>({
  value,
  save,
  equals,
}: UseInlineEditArgs<T>): InlineEditState<T> & InlineEditActions<T> {
  const [state, setState] = useState<InlineEditState<T>>(() => ({
    status: "idle",
    draft: value,
    error: null,
  }));

  // Keep a ref to the current committed value so commit() can detect
  // "nothing changed" without capturing a stale closure on first render.
  const valueRef = useRef<T>(value);
  valueRef.current = value;

  // Mirror the latest state into a ref so commit() can read the current
  // draft without racing with React's setState batching (the previous
  // "peek via setState callback" pattern occasionally saw undefined).
  const stateRef = useRef<InlineEditState<T>>(state);
  stateRef.current = state;

  const eq = equals ?? ((a: T, b: T) => a === b);

  const beginEdit = useCallback(() => {
    setState((prev) =>
      prev.status === "saving"
        ? prev
        : { status: "editing", draft: valueRef.current, error: null },
    );
  }, []);

  const updateDraft = useCallback((next: T) => {
    setState((prev) => ({ ...prev, draft: next, error: null }));
  }, []);

  const cancel = useCallback(() => {
    setState({ status: "idle", draft: valueRef.current, error: null });
  }, []);

  const commit = useCallback(async (): Promise<boolean> => {
    const draftSnapshot = stateRef.current.draft;
    // If nothing changed, skip the save round-trip.
    if (eq(draftSnapshot, valueRef.current)) {
      setState((prev) => ({ ...prev, status: "idle", error: null }));
      return true;
    }
    setState((prev) => ({ ...prev, status: "saving", error: null }));
    try {
      await save(draftSnapshot);
      setState((prev) => ({ ...prev, status: "idle", error: null }));
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setState((prev) => ({
        status: "editing",
        draft: prev.draft,
        error: message,
      }));
      return false;
    }
  }, [save, eq]);

  return { ...state, beginEdit, updateDraft, commit, cancel };
}
