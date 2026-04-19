import { useEffect, useRef } from "react";
import { useInlineEdit } from "./useInlineEdit";

export interface EditableTextProps {
  /** Current committed value from the server. */
  value: string;
  /** Called when the user commits a change — must throw on failure. */
  onSave: (next: string) => Promise<void>;
  /** Placeholder shown in read mode when ``value`` is empty. */
  placeholder?: string;
  /** Optional wrapper className in read mode. */
  className?: string;
  /** Optional input className in edit mode. */
  inputClassName?: string;
  /** Accessibility label (used as the input's aria-label). */
  ariaLabel: string;
  /** When true, the field is not clickable. Useful during network failures
   *  or when the parent is re-fetching. */
  disabled?: boolean;
}

/**
 * Single-line click-to-edit text. Enter commits, Esc cancels, blur commits.
 *
 * The component is deliberately unstyled beyond the minimum required for
 * keyboard interaction — each canvas node wraps it with its own typography
 * so the inline editor looks like the read-mode content rather than a
 * generic form input.
 */
export function EditableText({
  value,
  onSave,
  placeholder,
  className,
  inputClassName,
  ariaLabel,
  disabled,
}: EditableTextProps) {
  const edit = useInlineEdit<string>({ value, save: onSave });
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (edit.status === "editing" && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [edit.status]);

  const isEditing = edit.status === "editing" || edit.status === "saving";

  if (!isEditing) {
    const hasValue = value && value.trim().length > 0;
    return (
      <span
        className={className}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label={`${ariaLabel}. Click to edit.`}
        onClick={() => {
          if (!disabled) edit.beginEdit();
        }}
        onKeyDown={(e) => {
          if (disabled) return;
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            edit.beginEdit();
          }
        }}
        data-editable={disabled ? "disabled" : "idle"}
      >
        {hasValue ? value : <span className="italic text-slate-400">{placeholder ?? "(empty — click to edit)"}</span>}
      </span>
    );
  }

  return (
    <span className="inline-flex flex-col gap-1">
      <input
        ref={inputRef}
        type="text"
        value={edit.draft}
        onChange={(e) => edit.updateDraft(e.target.value)}
        onBlur={() => {
          // Don't commit if the user just clicked Save/Cancel (those
          // handlers stopPropagation); otherwise blur commits.
          if (edit.status === "editing") {
            void edit.commit();
          }
        }}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            void edit.commit();
          } else if (e.key === "Escape") {
            e.preventDefault();
            edit.cancel();
          }
        }}
        className={inputClassName ?? "w-full rounded border border-slate-300 px-1.5 py-0.5 text-sm focus:border-indigo-600 focus:outline-none"}
        aria-label={ariaLabel}
        aria-invalid={edit.error ? true : undefined}
        disabled={edit.status === "saving"}
      />
      {edit.status === "saving" && (
        <span className="text-[10px] text-slate-500" role="status">
          saving…
        </span>
      )}
      {edit.error && (
        <span className="text-[10px] text-rose-700" role="alert">
          ⚠ {edit.error}
        </span>
      )}
    </span>
  );
}
