import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { EditableText } from "../src/edit/EditableText";

describe("EditableText", () => {
  it("enters edit mode on click and saves on Enter", async () => {
    const user = userEvent.setup();
    const save = vi.fn().mockResolvedValue(undefined);

    render(<EditableText value="old" onSave={save} ariaLabel="Role name" />);

    await user.click(screen.getByRole("button", { name: /Role name/i }));
    const input = screen.getByRole("textbox", { name: "Role name" });
    await user.clear(input);
    await user.type(input, "new");
    await user.keyboard("{Enter}");

    expect(save).toHaveBeenCalledWith("new");
  });

  it("cancels on Escape without saving", async () => {
    const user = userEvent.setup();
    const save = vi.fn().mockResolvedValue(undefined);

    render(<EditableText value="old" onSave={save} ariaLabel="Role name" />);

    await user.click(screen.getByRole("button", { name: /Role name/i }));
    const input = screen.getByRole("textbox", { name: "Role name" });
    await user.type(input, "WILL-DISCARD");
    await user.keyboard("{Escape}");

    expect(save).not.toHaveBeenCalled();
    // Back to read mode.
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.getByText("old")).toBeInTheDocument();
  });

  it("shows an error banner when save rejects and keeps the draft", async () => {
    const user = userEvent.setup();
    const save = vi.fn().mockRejectedValue(new Error("server rejected"));

    render(<EditableText value="old" onSave={save} ariaLabel="Field" />);

    await user.click(screen.getByRole("button", { name: /Field/i }));
    const input = screen.getByRole("textbox", { name: "Field" });
    await user.clear(input);
    await user.type(input, "bad");
    await user.keyboard("{Enter}");

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/server rejected/);
    });
    // Still editing, input retains the value so the user can retry.
    expect((screen.getByRole("textbox", { name: "Field" }) as HTMLInputElement).value).toBe("bad");
  });

  it("shows placeholder when value is empty in read mode", () => {
    render(
      <EditableText
        value=""
        onSave={vi.fn()}
        placeholder="click to add"
        ariaLabel="Description"
      />,
    );
    expect(screen.getByText("click to add")).toBeInTheDocument();
  });

  it("doesn't open edit mode when disabled", async () => {
    const user = userEvent.setup();
    render(
      <EditableText value="x" onSave={vi.fn()} ariaLabel="Field" disabled />,
    );
    await user.click(screen.getByRole("button"));
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });
});
