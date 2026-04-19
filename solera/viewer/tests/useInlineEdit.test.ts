import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useInlineEdit } from "../src/edit/useInlineEdit";

describe("useInlineEdit", () => {
  it("starts in idle status", () => {
    const { result } = renderHook(() =>
      useInlineEdit<string>({ value: "a", save: async () => {} }),
    );
    expect(result.current.status).toBe("idle");
    expect(result.current.draft).toBe("a");
  });

  it("beginEdit → editing; updateDraft updates the draft", () => {
    const { result } = renderHook(() =>
      useInlineEdit<string>({ value: "a", save: async () => {} }),
    );
    act(() => result.current.beginEdit());
    expect(result.current.status).toBe("editing");
    act(() => result.current.updateDraft("b"));
    expect(result.current.draft).toBe("b");
  });

  it("commit with unchanged draft skips save and returns to idle", async () => {
    const save = vi.fn();
    const { result } = renderHook(() =>
      useInlineEdit<string>({ value: "a", save }),
    );
    act(() => result.current.beginEdit());
    await act(async () => {
      await result.current.commit();
    });
    expect(save).not.toHaveBeenCalled();
    expect(result.current.status).toBe("idle");
  });

  it("commit with changed draft calls save and returns to idle on success", async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const { result } = renderHook(() =>
      useInlineEdit<string>({ value: "a", save }),
    );
    act(() => result.current.beginEdit());
    act(() => result.current.updateDraft("b"));
    await act(async () => {
      await result.current.commit();
    });
    expect(save).toHaveBeenCalledWith("b");
    expect(result.current.status).toBe("idle");
  });

  it("commit with rejected save stays in editing with error", async () => {
    const save = vi.fn().mockRejectedValue(new Error("nope"));
    const { result } = renderHook(() =>
      useInlineEdit<string>({ value: "a", save }),
    );
    act(() => result.current.beginEdit());
    act(() => result.current.updateDraft("b"));
    await act(async () => {
      await result.current.commit();
    });
    expect(result.current.status).toBe("editing");
    expect(result.current.error).toBe("nope");
    expect(result.current.draft).toBe("b"); // keep the typed value
  });

  it("cancel reverts to idle and restores the committed value", () => {
    const { result } = renderHook(() =>
      useInlineEdit<string>({ value: "a", save: async () => {} }),
    );
    act(() => result.current.beginEdit());
    act(() => result.current.updateDraft("b"));
    act(() => result.current.cancel());
    expect(result.current.status).toBe("idle");
    expect(result.current.draft).toBe("a");
  });

  it("uses custom equality for list values", async () => {
    const save = vi.fn();
    const { result } = renderHook(() =>
      useInlineEdit<string[]>({
        value: ["a", "b"],
        save,
        equals: (x, y) => x.join("|") === y.join("|"),
      }),
    );
    act(() => result.current.beginEdit());
    // Functionally identical array — should skip the save.
    act(() => result.current.updateDraft(["a", "b"]));
    await act(async () => {
      await result.current.commit();
    });
    expect(save).not.toHaveBeenCalled();
  });
});
